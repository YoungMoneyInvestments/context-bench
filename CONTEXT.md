# Context Bench

Benchmarks whether a given piece of agent context (a CLAUDE.md, a skill, a system prompt) actually
makes a model's output *better* — or just makes the model quieter about doing what it would have
done anyway. Inspired by Boris Cherny's "delete your skills, delete your CLAUDE.md, see what
happens" advice.

## Language

**Case**:
A single fixed task (prompt + rubric) that every Profile is run against, e.g. "write a resource
guide from a transcript." Cases live as one YAML file each under `cases/`.
_Avoid_: Test, prompt, question

**Profile**:
One (Model, Context Bundle) pair under test, e.g. "Opus 5 + bare" or "Grok 4 + full context."
Runs are always reported per-Profile, never per-Model alone — the whole point is that the same
model can score differently depending on its Context Bundle.
_Avoid_: Config, variant, setup

**Model**:
An underlying provider endpoint (`anthropic:claude-opus-5`, `xai:grok-4`, …). A Model is one half
of a Profile; on its own it says nothing about how the request was framed.
_Avoid_: Provider (Provider is the API vendor; a Model is a specific endpoint on that Provider)

**Context Bundle**:
The system prompt (and, later, tool list) attached to a request before a Case is run. Two kinds:
`bare` (empty system prompt, no tools) and a directory of markdown files concatenated together
(`--context-dir`). `examples/context/` ships one synthetic demo bundle; a real user's own
CLAUDE.md/skills directory is never committed to this repo — see
[ADR 0001](./docs/adr/0001-context-bundles-are-pointers-not-committed-files.md).
_Avoid_: Skill, CLAUDE.md (those are *inputs* a user points a Context Bundle at, not the concept
itself)

**Run**:
The recorded result of executing one Case under one Profile once: raw output text, latency,
token usage, timestamp. Immutable once written — re-running produces a new Run, never an edit.
_Avoid_: Result, response

**Judge**:
A Model (kept separate from the Models under test, to reduce self-preference bias) that scores a
Run against its Case's rubric, blind to which Profile produced it.
_Avoid_: Grader, evaluator

**Judgment**:
A Judge's score (1-10) plus one-sentence reasoning for a single Run. Many Judgments (one per Run)
roll up into a Leaderboard.
_Avoid_: Score (Score is a field on a Judgment, not the concept itself)

**Leaderboard**:
The mean Judgment score per Profile, aggregated across all Cases in a run, rendered as a markdown
table. This is the only artifact meant for humans to read directly — Runs and Judgments are the
evidence underneath it.
_Avoid_: Results, report
