# context-bench

Score whether your skills, hooks, and memory still help — on Claude, Codex, Grok, or any model with a context pile. Then see which class newer models have outgrown.

```bash
pip install -e .
python3 -m contextbench.cli --context-dir ~/.claude   # Claude Code
python3 -m contextbench.cli --context-dir ~/.codex    # Codex
python3 -m contextbench.cli --context-dir ~/.grok     # Grok
```

Point it at whatever directory that provider uses for skills, hooks, or memory — Claude Code, Codex, Grok, or any other LLM tool with a context/memory pile. On a Claude-style home it **splits the pile** (`CLAUDE.md` / `skills` / `hooks` / `agents`), scores each class **alone** against bare, and prints a model × class table. Same idea on Codex or Grok: bare versus your skills and hooks. Read down a column. If a stronger model is worse on `hooks`, that is the class to delete when you upgrade.

<p align="center">
  <a href="https://github.com/YoungMoneyInvestments/context-bench/blob/master/docs/assets/context-bench.mp4">
    <img src="docs/assets/film-poster.jpg" alt="Watch the 51s film: Boris Cherny, then skills and hooks on Claude, Codex, and Grok" width="100%" />
  </a>
</p>

[51s film (play on GitHub)](https://github.com/YoungMoneyInvestments/context-bench/blob/master/docs/assets/context-bench.mp4) · [raw mp4](https://github.com/YoungMoneyInvestments/context-bench/raw/master/docs/assets/context-bench.mp4) · [9:16](https://github.com/YoungMoneyInvestments/context-bench/blob/master/docs/assets/context-bench-9x16.mp4)

<p align="center">
  <img src="docs/assets/loop.svg" alt="Each class of your Claude home is scored alone against bare, across models. Fading means stronger models get less lift." width="100%" />
</p>

| Call | When |
|---|---|
| **KEEP** | Δ ≥ +1.5 — that class earns its tokens |
| **PROMPT_BLOAT** | in between — barely moved the score |
| **REMOVE** | Δ ≤ −1.0 — the model got worse with it |
| **fading** | stronger models get less lift than weaker ones — they need that class less |

Boris Cherny told a YC room to delete `CLAUDE.md`, skills, and hooks every six months and see what the model does. [Nate Herk's video](https://youtu.be/XNQBCRcwXV4) is what made that advice circulate. A whole-directory delta only tells you the pile is heavy. The class table tells you **which kind** is the weight.

## Example

A smoke run of the synthetic demo bundle (`examples/context`) against six Cases — one blob, no classes, because that folder is not a Claude home:

| Model | Bare | +example | Δ | Call |
|---|---|---|---|---|
| Haiku 4.5 | 8.83 | 8.67 | −0.17 | PROMPT_BLOAT |
| Sonnet 5 | 8.83 | 9.17 | +0.33 | PROMPT_BLOAT |
| Opus 5 | 8.17 | 9.00 | +0.83 | PROMPT_BLOAT |

Against `~/.claude` the leaderboard opens with a **class matrix** instead: one row per `claude.md` / `skills` / `hooks` / `agents`, one column per model, a trend when Haiku still wants something Opus does not.

`--split families` groups skills by name prefix (`brokerbridge-*`). `--split skills` is one row per skill directory — expensive, use `--models opus` first.

## Quickstart

No API key for Claude Profiles or the judge — they use your local `claude` CLI (`claude /login`).

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .

# Synthetic demo first
python3 -m contextbench.cli --smoke

# The run that matters — auto-splits a Claude-style home
python3 -m contextbench.cli --context-dir ~/.claude

# Same bench against Codex or Grok (or any other skills/hooks/memory dir)
python3 -m contextbench.cli --context-dir ~/.codex
python3 -m contextbench.cli --context-dir ~/.grok

# One class family, one model
python3 -m contextbench.cli --context-dir ~/.claude --split families --models opus

# One skill at a time (slash-invokes the real Claude Code skill — not a SKILL.md dump)
python3 -m contextbench.cli --context-dir ~/.claude/skills/caveman --harness skill --models haiku

# Subscription CLIs (no API keys)
python3 -m contextbench.cli --models sonnet,haiku,grok,codex,cursor,gemini --smoke
```

`export XAI_API_KEY=...` optionally adds Grok (`--models xai:grok-4`).

Writes `results/runs_<ts>.json`, `results/judged_<ts>.json`, and `results/leaderboard_<ts>.md`.

The leaderboard leads with the class matrix, then mean scores, Arena-style Elo (within-run only), and bootstrap CIs on the deltas.

### Flags

| Flag | What it does |
|---|---|
| `--context-dir PATH` | Bundle to test. Repeatable. Default: `examples/context`. |
| `--split auto` | Default. A Claude home becomes `+all` plus `claude.md` / `skills` / `hooks` / `agents`. |
| `--split classes` | Force that four-class split. |
| `--split families` | Skills grouped by shared name prefix. |
| `--split skills` | One profile per skill directory. |
| `--split off` | Whole directory as one blob. |
| `--wrap fair` | Default. Case is the user message; skills and hooks are optional system context. |
| `--wrap system` | Skills and hooks as a raw system prompt. |
| `--wrap raw` | Old `"System Instructions:"` user-turn wrap ([issue #1](https://github.com/YoungMoneyInvestments/context-bench/issues/1)). |
| `--harness auto` | Default. Skill dirs (`SKILL.md`) use slash-invoke; prose dirs use notes wrap. |
| `--harness skill` | Force slash-invoke (`claude -p /skillname`). Bare arm gets `--disable-slash-commands`. |
| `--harness notes` | Always dump markdown as notes (old behavior). |
| `--models opus,sonnet,haiku` | Also: `grok`, `codex`, `cursor`, `gemini`, or `provider:model-id`. |
| `--smoke` | First Case × first model. Use this before a 6×3×N burn. |

## Read the numbers honestly

The judge is a model call, not ground truth. Read a few `results/judged_*.json` reasons before trusting a delta. Ten Cases is a smoke bench, not a statistically powered one. If a Profile swings on 1–2 Cases, that is noise.

**Skill dirs use real Claude Code slash-invoke by default** (`--harness auto` / `--harness skill`): `claude -p /skillname` with the Case as the rest of the prompt. That is the fair skill-ablation path ([ADR 0004](./docs/adr/0004-fair-cli-wrapping.md)). Prose bundles (`CLAUDE.md`, `examples/context`) still use notes wrap. `--harness notes` forces the old dump for either.

**Hooks that are only code** are inventoried as names, not executed. The class still shows up. A hook that never writes markdown cannot be scored as context — it is scored as "does reminding the model these hooks exist help," which is a weak test and labeled that way.

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

A whole-home REMOVE is not actionable. "hooks are fading on Opus, skills still pay on Haiku" is.

Source clips in the film: [Boris at YC Startup School](https://www.youtube.com/watch?v=qyPCVqFUyDo) · [Nate Herk](https://youtu.be/XNQBCRcwXV4). Short attributed excerpts; the rest is this project's explainer.

## License

MIT
