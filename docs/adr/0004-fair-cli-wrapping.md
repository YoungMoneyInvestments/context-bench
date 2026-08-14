# Fair CLI wrapping: task is the user message

## Context

Issue #1: dumping a real `SKILL.md` into `claude -p` as

```
System Instructions:
{skill.md}

Task:
{case prompt}
```

made Opus 5 / Sonnet 5 refuse the Case (injection suspicion, skill help-text, "no actual task"). Haiku still attempted the work. The resulting `REMOVE` verdicts were a wrapping artifact, not evidence the skill is harmful inside Claude Code.

## Decision

- Default wrap mode is `fair`: the Case is the user message. Bundle notes go through `claude --system-prompt-file` (or the API `system` role) behind a short preamble that says they are optional reference and must not block the task.
- `--wrap system` sends the notes as a raw system prompt (right for CLAUDE.md-shaped prose).
- `--wrap raw` reproduces the old user-turn stuffing so the bug is still measurable.
- `--context-dir PATH` (repeatable) is how you point the bench at your own bundle. ADR 0001 already described this flag; the CLI now actually has it.

## Consequences

This is still not a Claude Code skill-invocation test. `SKILL.md` files are written for a structured Skill tool, not for a one-shot system prompt. Fair wrap stops the false "model refused" collapse; it does not claim a skill works the same way it would under `/skill` or auto-invocation. A real harness loop remains future work.

`--bare` on the Claude CLI still cannot give a clean-room baseline under OAuth (ADR 0003). We do not pass that flag.
