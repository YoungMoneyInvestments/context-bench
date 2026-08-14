# context-bench

Score whether a `CLAUDE.md` or skill bundle actually helps a model — or just spends tokens.

```bash
pip install -e .
python3 -m contextbench.cli --context-dir ~/.claude
```

Same fixed **Cases** (prompt + rubric). Two **Profiles** per model: `bare` versus `+your-dir`. A separate model **judges** every answer against the rubric and never sees which Profile wrote it. The leaderboard is the delta.

<p align="center">
  <img src="docs/assets/loop.svg" alt="Case times Profile, then a blind judge, then KEEP, PROMPT_BLOAT, or REMOVE" width="100%" />
</p>

| Call | When |
|---|---|
| **KEEP** | Δ ≥ +1.5 — the bundle earns its tokens |
| **PROMPT_BLOAT** | in between — it barely moved the score |
| **REMOVE** | Δ ≤ −1.0 — the model got worse with the notes |

Boris Cherny told a YC room to delete `CLAUDE.md`, skills, and hooks every six months and see what the model does. [Nate Herk's video](https://youtu.be/XNQBCRcwXV4) is what made that advice circulate. People have been doing it as a vibe check. This repo is the vibe check with a rubric.

**Film (Boris clip, then the bench):** [`docs/assets/context-bench.mp4`](docs/assets/context-bench.mp4) · vertical [`docs/assets/context-bench-9x16.mp4`](docs/assets/context-bench-9x16.mp4)

## Example

A smoke run of the synthetic demo bundle (`examples/context`) against six Cases:

| Model | Bare | +example | Δ | Call |
|---|---|---|---|---|
| Haiku 4.5 | 8.83 | 8.67 | −0.17 | PROMPT_BLOAT |
| Sonnet 5 | 8.83 | 9.17 | +0.33 | PROMPT_BLOAT |
| Opus 5 | 8.17 | 9.00 | +0.83 | PROMPT_BLOAT |

None of those notes cleared KEEP. That is the point of measuring instead of guessing.

## Quickstart

No API key for Claude Profiles or the judge — they use your local `claude` CLI (`claude /login`).

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .

# Synthetic demo first
python3 -m contextbench.cli --smoke

# The run that matters
python3 -m contextbench.cli --context-dir ~/.claude

# One skill at a time
python3 -m contextbench.cli --context-dir ~/.claude/skills/caveman --models opus
```

`export XAI_API_KEY=...` optionally adds Grok (`--models xai:grok-4`).

Writes `results/runs_<ts>.json`, `results/judged_<ts>.json`, and `results/leaderboard_<ts>.md`.

### Flags

| Flag | What it does |
|---|---|
| `--context-dir PATH` | Bundle to test. Repeatable. Default: `examples/context`. |
| `--wrap fair` | Default. Case is the user message; notes are optional system context. |
| `--wrap system` | Notes as a raw system prompt. |
| `--wrap raw` | Old `"System Instructions:"` user-turn wrap ([issue #1](https://github.com/YoungMoneyInvestments/context-bench/issues/1)). |
| `--models opus,sonnet,haiku` | Or `provider:model-id`. |
| `--smoke` | First Case × first model. Use this before a 6×3×N burn. |

## Read the numbers honestly

The judge is a model call, not ground truth. Read a few `results/judged_*.json` reasons before trusting a delta. Six Cases is a smoke bench, not a statistically powered one. If a Profile swings on 1–2 Cases, that is noise.

**SKILL.md files are not invoked as Claude Code skills.** v1 concatenates markdown into a system prompt. That is the right test for a `CLAUDE.md`. It is the wrong test for a skill that should be called by name. `--wrap fair` stops Opus/Sonnet from treating the dump as a jailbreak ([ADR 0004](./docs/adr/0004-fair-cli-wrapping.md)).

**`bare` is not zero-context.** `claude -p` still loads your ambient `~/.claude` config on every Profile, including `bare`. The constant cancels out of the delta. Absolute scores are *your* scores ([ADR 0003](./docs/adr/0003-bare-is-relative-to-ambient-config-under-oauth.md)).

Vocabulary: [`CONTEXT.md`](./CONTEXT.md).

## Adding Cases

Drop a YAML file in `cases/`:

```yaml
category: coding
prompt: |
  <the task>
rubric:
  - <criterion the judge should check>
```

## Why

Anthropic deleted ~80% of Claude Code's own system prompt when Opus 5 shipped. The model got better. Boris's follow-up: do the same thing to *your* stack, on a six-month cadence, then add back only what you watch fail.

Source clips in the film: [Boris at YC Startup School](https://www.youtube.com/watch?v=qyPCVqFUyDo) · [Nate Herk](https://youtu.be/XNQBCRcwXV4). Short attributed excerpts; the rest is this project's explainer.

## License

MIT
