"""Core dataclasses. See CONTEXT.md for the vocabulary these implement."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Case:
    id: str
    category: str
    prompt: str
    rubric: list[str]


@dataclass
class Profile:
    id: str
    provider: str  # "anthropic" | "xai" | "openai"
    model: str  # provider-specific model id
    context_dir: str | None  # None => bare (empty system prompt)


@dataclass
class Run:
    case_id: str
    profile_id: str
    output: str
    latency_s: float
    input_tokens: int
    output_tokens: int
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Judgment:
    case_id: str
    profile_id: str
    score: int  # 1-10
    reasoning: str
    judge_model: str
