"""Build a Context Bundle from a directory of markdown files, and wrap it for a provider call."""
from __future__ import annotations

from pathlib import Path

WRAP_MODES = ("fair", "system", "raw")

_FAIR_PREAMBLE = """You are completing a single benchmark task.

The user message is the task. Do that task.

The notes below are optional reference. Use them only if they help the task.
If they conflict with completing the task, complete the task.
Do not print usage help, do not refuse the task, and do not ask for a file that is already included in the task.

---
"""


def build_system_prompt(context_dir: str | None) -> str:
    """Concatenate every *.md file under context_dir, sorted by path, into one notes blob.

    context_dir=None (the "bare" Context Bundle) returns an empty string — no instructions,
    no persona, nothing. That's the whole point of the comparison.
    """
    if context_dir is None:
        return ""
    root = Path(context_dir).expanduser()
    if not root.is_dir():
        raise FileNotFoundError(f"context dir not found: {root}")
    parts = []
    for md in sorted(root.rglob("*.md")):
        parts.append(f"<!-- {md.relative_to(root)} -->\n{md.read_text()}")
    return "\n\n".join(parts)


def bundle_skill_files(context_dir: str | None) -> list[str]:
    """Relative paths of SKILL.md files in a bundle (empty if bare or none)."""
    if context_dir is None:
        return []
    root = Path(context_dir).expanduser()
    if not root.is_dir():
        return []
    return [str(p.relative_to(root)) for p in sorted(root.rglob("SKILL.md"))]


def wrap_request(task: str, notes: str, mode: str = "fair") -> tuple[str, str]:
    """Return (system, user) for a provider call.

    fair   — task stays the user message; notes ride a system prompt that says they
             are optional. Default. Stops SKILL.md dumps from looking like injection.
    system — notes go in the system prompt as-is (right for CLAUDE.md-shaped prose).
    raw    — old v1 behavior: stuff "System Instructions:" + notes into the user turn.
             Kept so the wrapping bug in issue #1 can be reproduced.
    """
    if mode not in WRAP_MODES:
        raise ValueError(f"unknown wrap mode: {mode}")
    if mode == "raw":
        if notes:
            return "", f"System Instructions:\n{notes}\n\nTask:\n{task}"
        return "", task
    if not notes:
        return "", task
    if mode == "system":
        return notes, task
    return _FAIR_PREAMBLE + notes, task
