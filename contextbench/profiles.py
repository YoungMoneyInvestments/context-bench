"""Built-in Profile matrix: every Model crossed with bare vs example-context."""
from __future__ import annotations

from contextbench.models import Profile

_MODELS = [
    ("anthropic", "claude-opus-5"),
    ("anthropic", "claude-sonnet-5"),
    ("anthropic", "claude-haiku-4-5-20251001"),
    ("xai", "grok-4"),
]

_CONTEXT_DIRS = {
    "bare": None,
    "example": "examples/context",
}


def default_profiles() -> list[Profile]:
    profiles = []
    for provider, model in _MODELS:
        for bundle_name, context_dir in _CONTEXT_DIRS.items():
            profiles.append(
                Profile(id=f"{model}+{bundle_name}", provider=provider, model=model, context_dir=context_dir)
            )
    return profiles
