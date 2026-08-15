"""Offline --demo path: in-process mocks, no OAuth, no network."""
import json
import sys
from pathlib import Path
from unittest.mock import patch

from contextbench.cli import main
from contextbench.judge import _parse_verdict
from contextbench.providers import CALLERS, call_demo

REPO = Path(__file__).resolve().parent.parent
CASES = REPO / "cases"


def test_demo_registered_as_caller():
    assert CALLERS["demo"] is call_demo


def test_call_demo_is_deterministic():
    a = call_demo("demo-haiku", "notes", "summarize this")
    b = call_demo("demo-haiku", "notes", "summarize this")
    assert a == b
    assert a[0]
    assert a[1] > 0
    assert a[2] > 0


def test_call_demo_context_changes_output():
    bare = call_demo("demo-haiku", "", "summarize this")[0]
    with_notes = call_demo("demo-haiku", "Acme house style", "summarize this")[0]
    assert bare != with_notes
    assert "bare" in bare
    assert "Acme Labs" in with_notes


def test_call_demo_judge_returns_parseable_score():
    model_out = call_demo("demo-sonnet", "notes", "write a guide")[0]
    judge_prompt = (
        "You are grading a single AI response against a rubric.\n"
        "Rubric:\n- be clear\n"
        f"AI's response:\n---\n{model_out}\n---\n"
        'Reply with ONLY a JSON object: {"score": <1-10 integer>, "reasoning": "<one sentence>"}'
    )
    text, _, _ = call_demo("demo-judge", "", judge_prompt)
    score, reasoning = _parse_verdict(text)
    assert 1 <= score <= 10
    assert reasoning


def test_call_demo_does_not_use_subprocess_or_network():
    with (
        patch("subprocess.run") as mock_run,
        patch("urllib.request.urlopen") as mock_url,
    ):
        call_demo("demo-haiku", "sys", "do the task")
        judge_prompt = (
            "AI's response:\nhello\n"
            'Reply with ONLY a JSON object: {"score": 1, "reasoning": "x"}'
        )
        call_demo("demo-judge", "", judge_prompt)
        mock_run.assert_not_called()
        mock_url.assert_not_called()


def test_demo_cli_writes_artifacts_and_one_success_line(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(REPO)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "contextbench",
            "--demo",
            "--out-dir",
            str(tmp_path),
            "--cases-dir",
            str(CASES),
        ],
    )
    with (
        patch("subprocess.run") as mock_run,
        patch("urllib.request.urlopen") as mock_url,
    ):
        main()
        mock_run.assert_not_called()
        mock_url.assert_not_called()

    out_lines = [line for line in capsys.readouterr().out.splitlines() if line.strip()]
    assert len(out_lines) == 1
    dash = (tmp_path / "dashboard.html").resolve()
    assert str(dash) in out_lines[0]
    assert dash.is_file()

    runs = list(tmp_path.glob("runs_*.json"))
    judged = list(tmp_path.glob("judged_*.json"))
    boards = list(tmp_path.glob("leaderboard_*.md"))
    assert len(runs) == 1
    assert len(judged) == 1
    assert len(boards) == 1

    run_rows = json.loads(runs[0].read_text())
    judged_rows = json.loads(judged[0].read_text())
    assert run_rows
    assert judged_rows
    assert all(row.get("output") for row in run_rows)
    assert all(1 <= int(row["score"]) <= 10 for row in judged_rows)

    html = dash.read_text()
    assert "context-bench" in html
    assert "demo-haiku" in html or "demo-sonnet" in html


def test_demo_cli_limits_to_first_three_cases(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(REPO)
    monkeypatch.setattr(
        sys,
        "argv",
        ["contextbench", "--demo", "--out-dir", str(tmp_path), "--cases-dir", str(CASES)],
    )
    main()
    capsys.readouterr()
    run_rows = json.loads(next(tmp_path.glob("runs_*.json")).read_text())
    case_ids = {row["case_id"] for row in run_rows}
    assert len(case_ids) == 3
    expected = {p.stem for p in sorted(CASES.glob("*.yaml"))[:3]}
    assert case_ids == expected
