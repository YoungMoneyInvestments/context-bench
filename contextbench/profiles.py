"""Profile matrix: each Model crossed with bare plus one or more Context Bundles."""
from __future__ import annotations

import os
from pathlib import Path

from contextbench.models import Profile

_MODELS = [
    ("anthropic", "claude-opus-5"),
    ("anthropic", "claude-sonnet-5"),
    ("anthropic", "claude-haiku-4-5-20251001"),
]

MODEL_ALIASES = {
    "opus": ("anthropic", "claude-opus-5"),
    "sonnet": ("anthropic", "claude-sonnet-5"),
    "haiku": ("anthropic", "claude-haiku-4-5-20251001"),
    "claude-opus-5": ("anthropic", "claude-opus-5"),
    "claude-sonnet-5": ("anthropic", "claude-sonnet-5"),
    "claude-haiku-4-5-20251001": ("anthropic", "claude-haiku-4-5-20251001"),
}


def resolve_models(spec: str) -> list[tuple[str, str]]:
    """Parse 'opus,sonnet' or 'anthropic:claude-opus-5,xai:grok-4' into (provider, model) pairs."""
    out: list[tuple[str, str]] = []
    for raw in spec.split(","):
        token = raw.strip()
        if not token:
            continue
        if token in MODEL_ALIASES:
            out.append(MODEL_ALIASES[token])
        elif ":" in token:
            provider, model = token.split(":", 1)
            out.append((provider.strip(), model.strip()))
        else:
            raise ValueError(
                f"unknown model '{token}'. Use opus/sonnet/haiku or provider:model-id"
            )
    if not out:
        raise ValueError("no models specified")
    return out


def label_for_context_dir(context_dir: str) -> str:
    path = Path(context_dir).expanduser()
    return path.name or "context"


def default_profiles(
    *,
    context_dirs: list[tuple[str, str]] | None = None,
    models: list[tuple[str, str]] | None = None,
    provider: str | None = None,
    include_bare: bool = True,
) -> list[Profile]:
    """Build the Profile matrix.

    context_dirs: list of (label, path). None → the synthetic examples/context demo.
    provider: "auto" / None uses the CLI harness unless ANTHROPIC_API_KEY is set.
    """
    if models is None:
        models = list(_MODELS)
    if context_dirs is None:
        context_dirs = [("example", "examples/context")]

    if provider in (None, "auto"):
        use_cli = not os.environ.get("ANTHROPIC_API_KEY")
    else:
        use_cli = provider == "cli"

    profiles: list[Profile] = []
    for src_provider, model in models:
        effective = "cli" if use_cli else (provider if provider not in (None, "auto") else src_provider)
        if include_bare:
            profiles.append(
                Profile(id=f"{model}+bare", provider=effective, model=model, context_dir=None)
            )
        for label, context_dir in context_dirs:
            profiles.append(
                Profile(
                    id=f"{model}+{label}",
                    provider=effective,
                    model=model,
                    context_dir=context_dir,
                )
            )
    return profiles
