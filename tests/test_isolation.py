"""Isolation, fail-closed matrix, and packaged fixtures."""
from pathlib import Path
from unittest.mock import patch

from contextbench.cases import load_cases
from contextbench.cli import _expand_dirs
from contextbench.context import build_system_prompt
from contextbench.models import Case, Profile, Run
from contextbench.paths import bundled_cases_dir, resolve_cases_dir
from contextbench.runner import complete_matrix, run_all


def test_bundled_cases_resolve_when_cwd_has_none(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    resolved = resolve_cases_dir("cases")
    assert resolved == bundled_cases_dir()
    assert load_cases("cases")


def test_symlink_escape_is_rejected(tmp_path):
    root = tmp_path / "bundle"
    root.mkdir()
    secret = tmp_path / "outside.md"
    secret.write_text("SECRET")
    link = root / "leak.md"
    link.symlink_to(secret)
    try:
        build_system_prompt(str(root))
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "outside context dir" in str(exc)


def test_complete_matrix_reports_failed_cell():
    cases = [Case("c1", "x", "p", ["r"])]
    profiles = [
        Profile("m+bare", "demo", "m", None),
        Profile("m+ctx", "demo", "m", "examples/context"),
    ]
    runs = [
        Run("c1", "m+bare", "ok", 0.1, 1, 1),
        Run("c1", "m+ctx", "", 0.0, 0, 0, error="boom"),
    ]
    ok, missing = complete_matrix(cases, profiles, runs)
    assert ok is False
    assert missing == ["c1 x m+ctx"]


def test_run_all_records_unknown_provider():
    cases = [Case("c1", "x", "do it", ["r"])]
    profiles = [Profile("m+bare", "not-a-provider", "m", None)]
    runs = run_all(cases, profiles, verbose=False)
    assert len(runs) == 1
    assert runs[0].error
    ok, missing = complete_matrix(cases, profiles, runs)
    assert ok is False
    assert missing == ["c1 x m+bare"]


def test_split_skills_uses_the_skill_directory(tmp_path):
    home = tmp_path / "home"
    skill = home / "skills" / "example-skill"
    skill.mkdir(parents=True)
    (home / "CLAUDE.md").write_text("# house")
    (skill / "SKILL.md").write_text("# skill")
    bundles = _expand_dirs([str(home)], "skills")
    skill_bundles = [b for b in bundles if b[0].endswith("example-skill") or b[0] == "skills/example-skill"]
    assert skill_bundles
    assert Path(skill_bundles[0][1]).resolve() == skill.resolve()


def test_xai_without_key_does_not_call_claude(monkeypatch):
    from contextbench.providers import call_xai

    monkeypatch.delenv("XAI_API_KEY", raising=False)
    with patch("contextbench.providers.call_cli_harness") as mock_cli:
        try:
            call_xai("grok-4", "", "task")
            assert False, "expected RuntimeError"
        except RuntimeError as exc:
            assert "XAI_API_KEY" in str(exc)
        mock_cli.assert_not_called()
