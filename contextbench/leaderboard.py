from __future__ import annotations

from collections import defaultdict

from contextbench.models import Judgment


def aggregate(judgments: list[Judgment]) -> list[tuple[str, float, int]]:
    """Returns (profile_id, mean_score, n_cases) sorted best-first. Excludes unparseable (score=0)
    judgments from the mean but still counts them toward n_cases via their own row context."""
    by_profile: dict[str, list[int]] = defaultdict(list)
    for j in judgments:
        if j.score > 0:
            by_profile[j.profile_id].append(j.score)
    rows = [(pid, sum(scores) / len(scores), len(scores)) for pid, scores in by_profile.items() if scores]
    return sorted(rows, key=lambda r: r[1], reverse=True)


def to_markdown(judgments: list[Judgment]) -> str:
    rows = aggregate(judgments)
    lines = ["| Profile | Mean score | Cases judged |", "|---|---|---|"]
    for pid, mean, n in rows:
        lines.append(f"| `{pid}` | {mean:.1f} | {n} |")
    return "\n".join(lines)
