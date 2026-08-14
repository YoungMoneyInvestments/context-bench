"""Unit tests for contextbench ablation and leaderboard formatting."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from contextbench.ablation import VERDICT_HELPS, VERDICT_HURTS, VERDICT_NO_LIFT, analyze_deltas, verdict_for_delta
from contextbench.dashboard import _cell_class
from contextbench.leaderboard import aggregate, to_markdown
from contextbench.models import AblationDelta, Judgment, Profile


def test_aggregate_ranks_higher_mean_first():
    judgments = [
        Judgment("case1", "profileA", 8, "good", "judge"),
        Judgment("case2", "profileA", 6, "ok", "judge"),
        Judgment("case1", "profileB", 3, "bad", "judge"),
        Judgment("case2", "profileB", 5, "meh", "judge"),
    ]
    rows = aggregate(judgments)
    assert rows[0][0] == "profileA"
    assert rows[0][1] == 7.0
    assert rows[1][0] == "profileB"
    assert rows[1][1] == 4.0


def test_analyze_deltas_marks_hurts_when_context_lowers_score():
    profiles = [
        Profile("claude-opus-5+bare", "anthropic", "claude-opus-5", None),
        Profile("claude-opus-5+example", "anthropic", "claude-opus-5", "examples/context"),
    ]
    judgments = [
        Judgment("case1", "claude-opus-5+bare", 9, "great", "judge"),
        Judgment("case2", "claude-opus-5+bare", 9, "great", "judge"),
        Judgment("case1", "claude-opus-5+example", 6, "hobbled", "judge"),
        Judgment("case2", "claude-opus-5+example", 6, "hobbled", "judge"),
    ]
    deltas = analyze_deltas(judgments, profiles)
    assert len(deltas) == 1
    assert deltas[0].recommendation == VERDICT_HURTS
    assert deltas[0].delta == -3.0


def test_verdict_for_delta_uses_plain_language():
    assert verdict_for_delta(1.5) == VERDICT_HELPS
    assert verdict_for_delta(0.2) == VERDICT_NO_LIFT
    assert verdict_for_delta(-1.0) == VERDICT_HURTS


def test_dashboard_colors_plain_verdicts():
    assert _cell_class("Helps") == "keep"
    assert _cell_class("No lift") == "bloat"
    assert _cell_class("Hurts") == "remove"


def test_to_markdown_includes_ablation_matrix():
    judgments = [Judgment("case1", "profileA", 7, "fine", "judge")]
    deltas = [
        AblationDelta("claude-opus-5", "example", 9.0, 6.0, -3.0, VERDICT_HURTS)
    ]
    md = to_markdown(judgments, deltas)
    assert "profileA" in md
    assert "Same model, with vs without the extra context" in md
    assert VERDICT_HURTS in md
    assert "KEEP" not in md
    assert "PROMPT_BLOAT" not in md
    assert "REMOVE" not in md


if __name__ == "__main__":
    test_aggregate_ranks_higher_mean_first()
    test_analyze_deltas_marks_hurts_when_context_lowers_score()
    test_to_markdown_includes_ablation_matrix()
    print("ok")
