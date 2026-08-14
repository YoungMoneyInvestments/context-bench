from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from contextbench.ablation import analyze_deltas
from contextbench.cases import load_cases
from contextbench.context import WRAP_MODES, bundle_skill_files
from contextbench.leaderboard import to_markdown
from contextbench.profiles import default_profiles, label_for_context_dir, resolve_models
from contextbench.runner import run_all, runs_to_dicts
from contextbench.judge import judge_all, judgments_to_dicts


def main() -> None:
    p = argparse.ArgumentParser(
        prog="contextbench",
        description="Score whether a context bundle helps a model, or just gets in the way.",
    )
    p.add_argument("--cases-dir", default="cases")
    p.add_argument("--out-dir", default="results")
    p.add_argument(
        "--context-dir",
        action="append",
        default=None,
        metavar="PATH",
        help="Context Bundle to test against bare. Repeatable. Default: examples/context",
    )
    p.add_argument(
        "--wrap",
        choices=WRAP_MODES,
        default="fair",
        help="How to attach the bundle. fair=default (task is the user message). "
        "system=notes as raw system prompt. raw=reproduce the old System-Instructions wrap.",
    )
    p.add_argument(
        "--models",
        default="opus,sonnet,haiku",
        help="Comma list: opus,sonnet,haiku or provider:model-id",
    )
    p.add_argument(
        "--provider",
        default="auto",
        help="auto (CLI unless ANTHROPIC_API_KEY is set), cli, anthropic, openai, xai, omniroute",
    )
    p.add_argument("--no-bare", action="store_true", help="skip the bare (no extra bundle) arm")
    p.add_argument("--smoke", action="store_true", help="first case × first model only")
    p.add_argument("--judge-provider", default=None)
    p.add_argument("--judge-model", default="claude-opus-5")
    p.add_argument("--no-judge", action="store_true", help="run only, skip scoring")
    args = p.parse_args()

    cases = load_cases(args.cases_dir)
    if not cases:
        raise SystemExit(f"no cases found in {args.cases_dir}")

    try:
        models = resolve_models(args.models)
    except ValueError as e:
        raise SystemExit(str(e)) from e

    if args.context_dir:
        context_dirs = [(label_for_context_dir(path), path) for path in args.context_dir]
    else:
        context_dirs = None

    if args.smoke:
        cases = cases[:1]
        models = models[:1]

    profiles = default_profiles(
        context_dirs=context_dirs,
        models=models,
        provider=args.provider,
        include_bare=not args.no_bare,
    )
    if not profiles:
        raise SystemExit("no profiles to run (did you pass --no-bare with no --context-dir?)")

    skill_hits = []
    for profile in profiles:
        for rel in bundle_skill_files(profile.context_dir):
            skill_hits.append(f"{profile.id}:{rel}")
    if skill_hits:
        print(
            "[cli] note: this run includes SKILL.md files. fair wrap stops them from looking "
            "like a jailbreak, but it is still not a Claude Code skill-invocation test. "
            "See docs/adr/0004-fair-cli-wrapping.md"
        )

    judge_provider = args.judge_provider
    if not judge_provider:
        judge_provider = "anthropic" if os.environ.get("ANTHROPIC_API_KEY") else "cli"

    runs = run_all(cases, profiles, wrap=args.wrap)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    run_path = out_dir / f"runs_{ts}.json"
    run_path.write_text(json.dumps(runs_to_dicts(runs), indent=2))
    print(f"[cli] wrote {run_path}")

    if args.no_judge or not runs:
        return

    cases_by_id = {c.id: c for c in cases}
    judgments = judge_all(runs, cases_by_id, judge_provider, args.judge_model)
    judged_path = out_dir / f"judged_{ts}.json"
    judged_path.write_text(json.dumps(judgments_to_dicts(judgments), indent=2))
    print(f"[cli] wrote {judged_path}")

    deltas = analyze_deltas(judgments, profiles)
    board = to_markdown(judgments, deltas)
    board_path = out_dir / f"leaderboard_{ts}.md"
    board_path.write_text(board + "\n")
    print(f"[cli] wrote {board_path}\n\n{board}")


if __name__ == "__main__":
    main()
