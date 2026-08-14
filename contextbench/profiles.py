"""Built-in Profile matrix: Model crossed bare vs example-context."""
from __future__ import annotations

import os
from contextbench.models import Profile

_MODELS = [
    ("anthropic", "claude-opus-5"),
    ("anthropic", "claude-sonnet-5"),
    ("anthropic", "claude-haiku-4-5-20251001"),
]

_CONTEXT_DIRS = {
    "bare": None,
    "example": "examples/context",
}


def default_profiles() -> list[Profile]:
    profiles = []
    # If no API key is present, fallback to local CLI harness execution
    use_cli = not os.environ.get("ANTHROPIC_API_KEY")

    for provider, model in _MODELS:
        effective_provider = "cli" if use_cli else provider
        for bundle_name, context_dir in _CONTEXT_DIRS.items():
            profiles.append(
                Profile(id=f"{model}+{bundle_name}", provider=effective_provider, model=model, context_dir=context_dir)
            )
    return profiles
