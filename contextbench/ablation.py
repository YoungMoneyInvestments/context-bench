"""Skill Ablation Matrix runner: tests individual skills N-minus-1 to identify hobbling vs helpful instructions."""
from __future__ import annotations

from pathlib import Path
from contextbench.models import AblationDelta, Case, Judgment, Profile
from contextbench.runner import run_all
from contextbench.judge import judge_all

# What extra context did to the score vs the same model with nothing extra attached.
VERDICT_HELPS = "Helps"
VERDICT_NO_LIFT = "No lift"
VERDICT_HURTS = "Hurts"


def verdict_for_delta(delta: float) -> str:
    if delta >= 1.5:
        return VERDICT_HELPS
    if delta <= -1.0:
        return VERDICT_HURTS
    return VERDICT_NO_LIFT


def analyze_deltas(judgments: list[Judgment], profiles: list[Profile]) -> list[AblationDelta]:
    """Calculates interference delta (Score_with_skill - Score_bare) per model and skill."""
    # Pair by case_id. Unpaired arms (bare on case A, treatment on case B) must
    # not produce a KEEP — that fabricated +9 in the public-release audit.
    by_case: dict[tuple[str, str], int] = {}
    for j in judgments:
        if j.score > 0:
            by_case[(j.case_id, j.profile_id)] = j.score

    deltas: list[AblationDelta] = []
    bare_profiles = {p.model: p for p in profiles if p.context_dir is None}
    skill_profiles = [p for p in profiles if p.context_dir is not None]

    for sp in skill_profiles:
        bare_p = bare_profiles.get(sp.model)
        if not bare_p:
            continue

        pairs: list[tuple[int, int]] = []
        case_ids = {cid for (cid, pid) in by_case if pid in (bare_p.id, sp.id)}
        for cid in case_ids:
            bare_s = by_case.get((cid, bare_p.id))
            skill_s = by_case.get((cid, sp.id))
            if bare_s is None or skill_s is None:
                continue
            pairs.append((bare_s, skill_s))

        if not pairs:
            continue

        bare_mean = sum(b for b, _ in pairs) / len(pairs)
        skill_mean = sum(s for _, s in pairs) / len(pairs)
        delta = round(skill_mean - bare_mean, 2)

        skill_name = sp.class_id or (Path(sp.context_dir).name if sp.context_dir else sp.id)
        deltas.append(
            AblationDelta(
                model=sp.model,
                skill_name=skill_name,
                bare_score=round(bare_mean, 2),
                with_skill_score=round(skill_mean, 2),
                delta=delta,
                recommendation=verdict_for_delta(delta),
                kind=sp.kind,
                n_paired=len(pairs),
            )
        )

    return sorted(deltas, key=lambda d: d.delta, reverse=True)
