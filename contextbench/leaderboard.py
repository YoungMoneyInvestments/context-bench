from __future__ import annotations

from collections import defaultdict

from contextbench.models import AblationDelta, Judgment


def aggregate(judgments: list[Judgment]) -> list[tuple[str, float, int]]:
    """Returns (profile_id, mean_score, n_cases) sorted best-first. Excludes unparseable (score=0)
    judgments from the mean but still counts them toward n_cases via their own row context."""
    by_profile: dict[str, list[int]] = defaultdict(list)
    for j in judgments:
        if j.score > 0:
            by_profile[j.profile_id].append(j.score)
    rows = [(pid, sum(scores) / len(scores), len(scores)) for pid, scores in by_profile.items() if scores]
    return sorted(rows, key=lambda r: r[1], reverse=True)


def to_markdown(judgments: list[Judgment], deltas: list[AblationDelta] | None = None) -> str:
    rows = aggregate(judgments)
    lines = [
        "# Context-Bench Leaderboard",
        "",
        "| Profile | Mean Score | Cases Judged |",
        "|---|---|---|",
    ]
    for pid, mean, n in rows:
        lines.append(f"| `{pid}` | {mean:.1f} | {n} |")

    if deltas:
        lines.extend([
            "",
            "## Skill Ablation & Recommendation Matrix",
            "",
            "| Model | Skill / Context | Bare Score | With Context | Delta (Δ) | Recommendation |",
            "|---|---|---|---|---|---|",
        ])
        for d in deltas:
            icon = "✅" if d.recommendation == "KEEP" else ("❌" if d.recommendation == "REMOVE" else "🧹")
            lines.append(
                f"| `{d.model}` | `{d.skill_name}` | {d.bare_score} | {d.with_skill_score} | {d.delta:+.2f} | {icon} **{d.recommendation}** |"
            )
        lines.extend([
            "",
            "**What to do about it** (this is whole-bundle Delta, not per-file — it tells you"
            " *whether* to cut, not *which lines*):",
            "- ✅ **KEEP** (Δ ≥ +1.5): clear win here, leave it as-is.",
            "- 🧹 **PROMPT_BLOAT** (-1.0 < Δ < +1.5): not clearly earning its token cost on these"
            " case types. Split the bundle into smaller files and re-run — the ones with Δ near"
            " zero on their own are what to cut first.",
            "- ❌ **REMOVE** (Δ ≤ -1.0): actively made the model worse here. Don't just delete it —"
            " read a couple of `results/judged_*.json` reasoning strings for this profile first;"
            " a large negative Δ is sometimes a harness artifact (e.g. issue #1's raw"
            " system-prompt wrapping) rather than the content itself being bad.",
        ])

    return "\n".join(lines)
