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
    """Paired per-case delta. No verdict unless every case has both arms."""
    by_cell: dict[tuple[str, str], int] = {}
    for j in judgments:
        if j.score > 0:
            by_cell[(j.case_id, j.profile_id)] = j.score

    case_ids = sorted({j.case_id for j in judgments})
    if not case_ids:
        return []

    bare_profiles = {p.model: p for p in profiles if p.context_dir is None}
    skill_profiles = [p for p in profiles if p.context_dir is not None]
    deltas: list[AblationDelta] = []

    for sp in skill_profiles:
        bare_p = bare_profiles.get(sp.model)
        if not bare_p:
            continue
        pairs: list[tuple[int, int]] = []
        for case_id in case_ids:
            bare_score = by_cell.get((case_id, bare_p.id))
            with_score = by_cell.get((case_id, sp.id))
            if bare_score is None or with_score is None:
                pairs = []
                break
            pairs.append((bare_score, with_score))
        if len(pairs) != len(case_ids):
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
                paired_n=len(pairs),
            )
        )

    return sorted(deltas, key=lambda d: d.delta, reverse=True)
