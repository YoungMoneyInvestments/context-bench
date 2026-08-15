from __future__ import annotations

import time
from dataclasses import asdict

from contextbench.context import build_system_prompt, wrap_request
from contextbench.models import Case, Profile, Run
from contextbench.providers import CALLERS


def run_one(
    case: Case,
    profile: Profile,
    wrap: str = "fair",
    *,
    disable_slash_baseline: bool = False,
) -> Run:
    del disable_slash_baseline  # isolated wrap path; --safe-mode is on the CLI caller
    start = time.monotonic()
    if profile.provider not in CALLERS:
        raise ValueError(f"unknown provider: {profile.provider}")
    notes = build_system_prompt(
        profile.context_dir,
        include=profile.include,
        extra_notes=profile.extra_notes,
    )
    system, user = wrap_request(case.prompt, notes, wrap)
    caller = CALLERS[profile.provider]
    text, in_tok, out_tok = caller(profile.model, system, user)
    latency = time.monotonic() - start
    return Run(
        case_id=case.id,
        profile_id=profile.id,
        output=text,
        latency_s=round(latency, 2),
        input_tokens=in_tok,
        output_tokens=out_tok,
    )


def run_all(
    cases: list[Case],
    profiles: list[Profile],
    wrap: str = "fair",
    *,
    disable_slash_baseline: bool | None = None,
    verbose: bool = True,
) -> list[Run]:
    """Sequential on purpose — a benchmark isn't a load test, and sequential runs are easy to
    read logs for. Parallelize later if the case/profile matrix gets big enough to matter."""
    runs = []
    for case in cases:
        for profile in profiles:
            if verbose:
                print(f"[run] {case.id} x {profile.id}")
            try:
                runs.append(
                    run_one(
                        case,
                        profile,
                        wrap=wrap,
                        disable_slash_baseline=bool(disable_slash_baseline),
                    )
                )
            except Exception as exc:  # noqa: BLE001 - record the cell, then fail closed
                if verbose:
                    print(f"[run] FAILED {case.id} x {profile.id}")
                runs.append(
                    Run(
                        case_id=case.id,
                        profile_id=profile.id,
                        output="",
                        latency_s=0.0,
                        input_tokens=0,
                        output_tokens=0,
                        error=_safe_error(exc),
                    )
                )
    return runs


def _safe_error(exc: BaseException) -> str:
    text = f"{type(exc).__name__}: {exc}"
    return text[:240]


def complete_matrix(
    cases: list[Case], profiles: list[Profile], runs: list[Run]
) -> tuple[bool, list[str]]:
    expected = {(case.id, profile.id) for case in cases for profile in profiles}
    ok = {(run.case_id, run.profile_id) for run in runs if not run.error}
    missing = sorted(expected - ok)
    return not missing, [f"{case_id} x {profile_id}" for case_id, profile_id in missing]


def runs_to_dicts(runs: list[Run]) -> list[dict]:
    return [asdict(r) for r in runs]
