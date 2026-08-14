"""Wrap modes and Profile construction."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from contextbench.context import bundle_skill_files, wrap_request
from contextbench.profiles import default_profiles, label_for_context_dir, resolve_models


def test_fair_wrap_keeps_task_as_user_message():
    system, user = wrap_request("fix the bug", "be terse", "fair")
    assert user == "fix the bug"
    assert "optional reference" in system
    assert "be terse" in system
    assert "System Instructions:" not in system
    assert "System Instructions:" not in user


def test_raw_wrap_reproduces_old_user_stuffing():
    system, user = wrap_request("fix the bug", "be terse", "raw")
    assert system == ""
    assert user.startswith("System Instructions:")
    assert "be terse" in user
    assert "Task:" in user


def test_system_wrap_is_notes_as_system():
    system, user = wrap_request("fix the bug", "be terse", "system")
    assert system == "be terse"
    assert user == "fix the bug"


def test_bare_notes_are_empty_in_every_mode():
    for mode in ("fair", "system", "raw"):
        system, user = wrap_request("fix the bug", "", mode)
        assert system == ""
        assert user == "fix the bug"


def test_resolve_models_aliases():
    assert resolve_models("opus") == [("anthropic", "claude-opus-5")]
    assert resolve_models("xai:grok-4") == [("xai", "grok-4")]


def test_label_for_context_dir_uses_basename():
    assert label_for_context_dir("examples/context") == "context"
    assert label_for_context_dir("~/.claude/skills/caveman") == "caveman"


def test_default_profiles_include_bare_and_named_bundle():
    profiles = default_profiles(
        context_dirs=[("demo", "examples/context")],
        models=[("anthropic", "claude-opus-5")],
        provider="anthropic",
        include_bare=True,
    )
    ids = [p.id for p in profiles]
    assert ids == ["claude-opus-5+bare", "claude-opus-5+demo"]
    assert profiles[0].context_dir is None
    assert profiles[1].context_dir == "examples/context"


def test_bundle_skill_files_finds_skill_md():
    with tempfile.TemporaryDirectory() as raw:
        tmp_path = Path(raw)
        (tmp_path / "SKILL.md").write_text("# skill")
        assert bundle_skill_files(str(tmp_path)) == ["SKILL.md"]
    assert bundle_skill_files(None) == []


if __name__ == "__main__":
    test_fair_wrap_keeps_task_as_user_message()
    test_raw_wrap_reproduces_old_user_stuffing()
    test_system_wrap_is_notes_as_system()
    test_bare_notes_are_empty_in_every_mode()
    test_resolve_models_aliases()
    test_label_for_context_dir_uses_basename()
    test_default_profiles_include_bare_and_named_bundle()
    test_bundle_skill_files_finds_skill_md()
    print("ok")
