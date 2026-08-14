from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from contextbench.ablation import analyze_deltas
from contextbench.cases import load_cases
from contextbench.leaderboard import to_markdown
from contextbench.models import Case, Judgment, Run
from contextbench.profiles import default_profiles
from contextbench.runner import run_all, runs_to_dicts
from contextbench.judge import judge_all, judgments_to_dicts


def main() -> None:
    p = argparse.ArgumentParser(prog="contextbench")
    p.add_argument("--cases-dir", default="cases")
    p.add_argument("--out-dir", default="results")
    p.add_argument("--judge-provider", default=None)
    p.add_argument("--judge-model", default="claude-opus-5")
    p.add_argument("--no-judge", action="store_true", help="run only, skip scoring")
    args = p.parse_args()

    cases = load_cases(args.cases_dir)
    if not cases:
        raise SystemExit(f"no cases found in {args.cases_dir}")
    profiles = default_profiles()

    judge_provider = args.judge_provider
    if not judge_provider:
        judge_provider = "anthropic" if os.environ.get("ANTHROPIC_API_KEY") else "cli"

    runs = run_all(cases, profiles)
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
