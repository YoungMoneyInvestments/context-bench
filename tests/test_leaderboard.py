"""No network calls. Run with: python3 tests/test_leaderboard.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from contextbench.leaderboard import aggregate, to_markdown
from contextbench.models import Judgment


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


def test_aggregate_excludes_unparseable_zero_scores():
    judgments = [
        Judgment("case1", "profileA", 0, "unparseable judge output", "judge"),
        Judgment("case2", "profileA", 9, "great", "judge"),
    ]
    rows = aggregate(judgments)
    assert rows == [("profileA", 9.0, 1)]


def test_to_markdown_produces_a_table_row_per_profile():
    judgments = [Judgment("case1", "profileA", 7, "fine", "judge")]
    md = to_markdown(judgments)
    assert "profileA" in md
    assert "7.0" in md


if __name__ == "__main__":
    test_aggregate_ranks_higher_mean_first()
    test_aggregate_excludes_unparseable_zero_scores()
    test_to_markdown_produces_a_table_row_per_profile()
    print("ok")
