from __future__ import annotations

import time
from dataclasses import asdict

from contextbench.context import build_system_prompt
from contextbench.models import Case, Profile, Run
from contextbench.providers import CALLERS


def run_one(case: Case, profile: Profile) -> Run:
    system = build_system_prompt(profile.context_dir)
    caller = CALLERS[profile.provider]
    start = time.monotonic()
    text, in_tok, out_tok = caller(profile.model, system, case.prompt)
    latency = time.monotonic() - start
    return Run(
        case_id=case.id,
        profile_id=profile.id,
        output=text,
        latency_s=round(latency, 2),
        input_tokens=in_tok,
        output_tokens=out_tok,
    )


def run_all(cases: list[Case], profiles: list[Profile]) -> list[Run]:
    """Sequential on purpose — a benchmark isn't a load test, and sequential runs are easy to
    read logs for. Parallelize later if the case/profile matrix gets big enough to matter."""
    runs = []
    for case in cases:
        for profile in profiles:
            print(f"[run] {case.id} x {profile.id}")
            try:
                runs.append(run_one(case, profile))
            except Exception as e:  # noqa: BLE001 - one bad profile/case shouldn't kill the run
                print(f"[run] FAILED {case.id} x {profile.id}: {e}")
    return runs


def runs_to_dicts(runs: list[Run]) -> list[dict]:
    return [asdict(r) for r in runs]
