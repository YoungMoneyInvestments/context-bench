"""Skill Ablation Matrix runner: tests individual skills N-minus-1 to identify hobbling vs helpful instructions."""
from __future__ import annotations

from pathlib import Path
from contextbench.models import AblationDelta, Case, Judgment, Profile
from contextbench.runner import run_all
from contextbench.judge import judge_all


def analyze_deltas(judgments: list[Judgment], profiles: list[Profile]) -> list[AblationDelta]:
    """Calculates interference delta (Score_with_skill - Score_bare) per model and skill."""
    from collections import defaultdict

    scores_by_profile: dict[str, list[int]] = defaultdict(list)
    for j in judgments:
        if j.score > 0:
            scores_by_profile[j.profile_id].append(j.score)

    profile_map = {p.id: p for p in profiles}
    deltas: list[AblationDelta] = []

    # Find bare profiles vs skill profiles
    bare_profiles = {p.model: p for p in profiles if p.context_dir is None}
    skill_profiles = [p for p in profiles if p.context_dir is not None]

    for sp in skill_profiles:
        model = sp.model
        bare_p = bare_profiles.get(model)
        if not bare_p:
            continue

        bare_scores = scores_by_profile.get(bare_p.id, [])
        skill_scores = scores_by_profile.get(sp.id, [])

        if not bare_scores or not skill_scores:
            continue

        bare_mean = sum(bare_scores) / len(bare_scores)
        skill_mean = sum(skill_scores) / len(skill_scores)
        delta = round(skill_mean - bare_mean, 2)

        if delta >= 1.5:
            rec = "KEEP"
        elif delta <= -1.0:
            rec = "REMOVE"
        else:
            rec = "PROMPT_BLOAT"

        skill_name = sp.class_id or (Path(sp.context_dir).name if sp.context_dir else sp.id)
        deltas.append(
            AblationDelta(
                model=model,
                skill_name=skill_name,
                bare_score=round(bare_mean, 2),
                with_skill_score=round(skill_mean, 2),
                delta=delta,
                recommendation=rec,
                kind=sp.kind,
            )
        )

    return sorted(deltas, key=lambda d: d.delta, reverse=True)
