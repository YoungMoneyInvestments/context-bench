from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from contextbench.ablation import analyze_deltas
from contextbench.cases import load_cases
from contextbench.classes import SPLIT_MODES, discover_classes, is_claude_home
from contextbench.context import WRAP_MODES, bundle_skill_files
from contextbench.leaderboard import to_markdown

try:
    from contextbench.elo import bootstrap_delta_ci, elo_ratings
except ImportError:  # Elo shipped in a parallel change; class split must run without it
    bootstrap_delta_ci = None
    elo_ratings = None
from contextbench.dashboard import write_dashboard
from contextbench.paths import (
    is_shipped_example,
    resolve_cases_dir,
    resolve_example_dir,
    write_private,
)
from contextbench.profiles import HARNESS_MODES, default_profiles, label_for_context_dir, resolve_models
from contextbench.providers import CALLERS
from contextbench.runner import complete_matrix, run_all, runs_to_dicts
from contextbench.judge import judge_all, judgments_to_dicts

DEMO_CASE_LIMIT = 3
DEMO_MODELS = "demo:demo-haiku,demo:demo-sonnet"
DEMO_PROVIDER = "demo"
DEMO_JUDGE_MODEL = "demo-judge"


def _run_demo(args: argparse.Namespace) -> None:
    """Offline mock bench: in-process fakes only, then a local dashboard."""
    cases = load_cases(str(resolve_cases_dir(args.cases_dir)))[:DEMO_CASE_LIMIT]
    if not cases:
        raise SystemExit(f"no cases found in {args.cases_dir}")

    models = resolve_models(DEMO_MODELS)
    profiles = default_profiles(
        context_dirs=[("example", str(resolve_example_dir()))],
        models=models,
        provider=DEMO_PROVIDER,
        include_bare=True,
        harness="notes",
    )
    runs = run_all(cases, profiles, wrap="fair", verbose=False)
    ok, missing = complete_matrix(cases, profiles, runs)
    if not ok:
        raise SystemExit("demo matrix incomplete: " + ", ".join(missing))

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(args.out_dir)
    write_private(out_dir / f"runs_{ts}.json", json.dumps(runs_to_dicts(runs), indent=2))

    cases_by_id = {c.id: c for c in cases}
    judgments = judge_all(
        runs, cases_by_id, DEMO_PROVIDER, DEMO_JUDGE_MODEL, verbose=False
    )
    write_private(
        out_dir / f"judged_{ts}.json",
        json.dumps(judgments_to_dicts(judgments), indent=2),
    )

    deltas = analyze_deltas(judgments, profiles)
    if not deltas:
        raise SystemExit("demo produced no paired verdicts")
    delta_ci = bootstrap_delta_ci(judgments, profiles) if bootstrap_delta_ci else None
    board = to_markdown(judgments, deltas, elo=None, delta_ci=delta_ci or None)
    board_path = out_dir / f"leaderboard_{ts}.md"
    write_private(board_path, board + "\n")

    dash = write_dashboard(board_path, out_dir / "dashboard.html")
    print(f"Demo ready: {dash.resolve()}")


def _expand_dirs(paths: list[str], split: str) -> list[tuple]:
    """Turn --context-dir paths into profile bundles. Auto-splits a Claude home."""
    bundles: list[tuple] = []
    for path in paths:
        mode = split
        if mode == "auto":
            mode = "classes" if is_claude_home(path) else "off"
        classes = discover_classes(path, mode) if mode != "off" else []
        if not classes:
            bundles.append((label_for_context_dir(path), path))
            continue
        print(
            f"[cli] {path} split into {len(classes)} classes: "
            + ", ".join(c.id for c in classes)
            + " (plus +all for the whole pile). --split off to disable."
        )
        bundles.append((label_for_context_dir(path) + "+all", path))
        for cls in classes:
            include = tuple(cls.files)
            if not include and not cls.extra_notes:
                continue
            if mode == "skills" and cls.kind == "skills" and include:
                skill_dir = str(Path(path).expanduser() / Path(include[0]).parent)
                bundles.append((cls.id, skill_dir))
                continue
            bundles.append(
                (cls.id, path, include, cls.extra_notes, cls.id, cls.kind)
            )
    return bundles


def _validate_plan(cases, profiles) -> None:
    ids = [profile.id for profile in profiles]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate profile ids")
    for profile in profiles:
        if profile.provider not in CALLERS:
            raise SystemExit(f"unknown provider: {profile.provider}")
        if profile.context_dir:
            root = Path(profile.context_dir).expanduser()
            if not root.is_dir():
                raise SystemExit(f"context dir not found: {root}")


def _confirm_private_context(profiles, *, yes: bool) -> None:
    private = [
        profile.context_dir
        for profile in profiles
        if profile.context_dir and not is_shipped_example(profile.context_dir)
    ]
    if not private:
        return
    if yes:
        return
    if not sys.stdin.isatty():
        raise SystemExit(
            "refusing to send a non-example context dir without --yes "
            "(this uploads the selected markdown to the model provider)"
        )
    print("[cli] about to send these context dirs to the model provider:")
    for path in sorted(set(private)):
        print(f"  {path}")
    answer = input("Continue? [y/N] ").strip().lower()
    if answer not in {"y", "yes"}:
        raise SystemExit("aborted")


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
        "--harness",
        choices=HARNESS_MODES,
        default="auto",
        help="auto=skill dirs use slash /skill invoke; notes=always system-prompt wrap; "
        "skill=require --context-dir to be skill dirs with SKILL.md.",
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
        help="auto=subscription CLI for Anthropic aliases. Billed APIs need an explicit name.",
    )
    p.add_argument(
        "--split",
        choices=SPLIT_MODES,
        default="auto",
        help="auto=split a Claude home (CLAUDE.md/skills/hooks/agents) into classes. "
        "classes=those four kinds. families=group skills by name prefix. "
        "skills=one profile per skill dir. off=one blob for the whole dir.",
    )
    p.add_argument("--no-bare", action="store_true", help="skip the bare (no extra bundle) arm")
    p.add_argument("--smoke", action="store_true", help="first case × first model only")
    p.add_argument(
        "--demo",
        action="store_true",
        help="offline in-process mock run (no OAuth, no API keys, no network)",
    )
    p.add_argument("--judge-provider", default=None)
    p.add_argument("--judge-model", default="claude-opus-5")
    p.add_argument("--no-judge", action="store_true", help="run only, skip scoring")
    p.add_argument(
        "--yes",
        action="store_true",
        help="send a non-example --context-dir without prompting",
    )
    args = p.parse_args()

    if args.demo:
        _run_demo(args)
        return

    cases = load_cases(str(resolve_cases_dir(args.cases_dir)))
    if not cases:
        raise SystemExit(f"no cases found in {args.cases_dir}")

    try:
        models = resolve_models(args.models)
    except ValueError as e:
        raise SystemExit(str(e)) from e

    if args.context_dir:
        context_dirs = _expand_dirs(args.context_dir, args.split)
    else:
        context_dirs = None

    if args.smoke:
        cases = cases[:1]
        models = models[:1]

    try:
        profiles = default_profiles(
            context_dirs=context_dirs,
            models=models,
            provider=args.provider,
            include_bare=not args.no_bare,
            harness=args.harness,
        )
    except ValueError as e:
        raise SystemExit(str(e)) from e
    if not profiles:
        raise SystemExit("no profiles to run (did you pass --no-bare with no --context-dir?)")
    _validate_plan(cases, profiles)
    _confirm_private_context(profiles, yes=args.yes)

    if args.harness != "notes":
        wrapped_skills = []
        for profile in profiles:
            wrapped_skills.extend(bundle_skill_files(profile.context_dir))
        if wrapped_skills:
            print(
                "[cli] isolated wrap: SKILL.md is extra system text under --safe-mode. "
                "This is not a live slash-invoke of the installed skill."
            )
    print("[cli] Claude CLI arms use --safe-mode so ambient ~/.claude does not load.")

    judge_provider = args.judge_provider or (
        args.provider if args.provider not in (None, "auto") else "cli"
    )
    if judge_provider not in CALLERS:
        raise SystemExit(f"unknown judge provider: {judge_provider}")

    runs = run_all(cases, profiles, wrap=args.wrap)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(args.out_dir)
    run_path = out_dir / f"runs_{ts}.json"
    write_private(run_path, json.dumps(runs_to_dicts(runs), indent=2))
    print(f"[cli] wrote {run_path}")

    ok, missing = complete_matrix(cases, profiles, runs)
    if not ok:
        print("[cli] incomplete matrix; not writing verdicts:")
        for item in missing:
            print(f"  missing {item}")
        raise SystemExit(1)

    if args.no_judge:
        return

    cases_by_id = {c.id: c for c in cases}
    judgments = judge_all(runs, cases_by_id, judge_provider, args.judge_model)
    judged_path = out_dir / f"judged_{ts}.json"
    write_private(judged_path, json.dumps(judgments_to_dicts(judgments), indent=2))
    print(f"[cli] wrote {judged_path}")

    deltas = analyze_deltas(judgments, profiles)
    if not deltas:
        print("[cli] no paired per-case deltas; not writing Helps/No lift/Hurts")
        raise SystemExit(1)
    delta_ci = bootstrap_delta_ci(judgments, profiles) if bootstrap_delta_ci else None
    board = to_markdown(judgments, deltas, elo=None, delta_ci=delta_ci or None)
    board_path = out_dir / f"leaderboard_{ts}.md"
    write_private(board_path, board + "\n")
    print(f"[cli] wrote {board_path}\n\n{board}")


if __name__ == "__main__":
    main()
