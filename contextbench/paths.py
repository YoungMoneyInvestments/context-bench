"""Resolve shipped fixtures so --demo works after a wheel install, from any cwd."""
from __future__ import annotations

import os
from pathlib import Path


def package_dir() -> Path:
    return Path(__file__).resolve().parent


def bundled_cases_dir() -> Path:
    return package_dir() / "bundled" / "cases"


def bundled_example_dir() -> Path:
    return package_dir() / "bundled" / "examples" / "context"


def resolve_cases_dir(cases_dir: str) -> Path:
    path = Path(cases_dir).expanduser()
    if path.is_dir() and any(path.glob("*.yaml")):
        return path
    bundled = bundled_cases_dir()
    if bundled.is_dir() and any(bundled.glob("*.yaml")):
        return bundled
    return path


def resolve_example_dir(context_dir: str | None = None) -> Path:
    if context_dir:
        path = Path(context_dir).expanduser()
        if path.is_dir():
            return path
    cwd = Path.cwd() / "examples" / "context"
    if cwd.is_dir():
        return cwd
    repo = package_dir().parent / "examples" / "context"
    if repo.is_dir():
        return repo
    return bundled_example_dir()


def is_shipped_example(path: str | Path) -> bool:
    text = str(Path(path).expanduser().resolve())
    return "examples/context" in text or "bundled/examples/context" in text


def write_private(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(path.parent, 0o700)
    except OSError:
        pass
    path.write_text(text)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
