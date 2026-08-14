# context-bench

Find which **skills** and **hooks** still help — and which newer models have outgrown.

Works on Claude Code, Codex, Grok, or any LLM tool with a skills / hooks / memory directory. It splits that pile, scores each class **alone** against bare, and prints KEEP / PROMPT_BLOAT / REMOVE.

**No API key to look around.** `--demo` is fully offline (in-process mocks, no OAuth). Real runs use your local `claude` CLI (`claude /login`). Optional: `XAI_API_KEY` for Grok.

## Run it

```bash
git clone https://github.com/YoungMoneyInvestments/context-bench.git
cd context-bench
```

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
python3 -m contextbench.cli --demo
open results/dashboard.html
```

### Real subscription / OAuth runs

```bash
# The run that matters
python3 -m contextbench.cli --context-dir ~/.claude
```

Same bench against Codex or Grok (or any other skills/hooks/memory dir):

```bash
python3 -m contextbench.cli --context-dir ~/.codex
python3 -m contextbench.cli --context-dir ~/.grok
```

On a Claude-style home it auto-splits `CLAUDE.md` / `skills` / `hooks` / `agents`. Read down a column. If a stronger model is worse on `hooks`, that is the class to delete when you upgrade.

| Call | When |
|---|---|
| **KEEP** | Δ ≥ +1.5 — that class earns its tokens |
| **PROMPT_BLOAT** | in between — barely moved the score |
| **REMOVE** | Δ ≤ −1.0 — the model got worse with it |
| **fading** | stronger models get less lift than weaker ones |

Writes `results/leaderboard_<ts>.md`. The leaderboard opens with a class matrix, then scores, Elo, and CIs.

<p align="center">
  <img src="docs/assets/loop.svg" alt="Shape of a class × model table: each class scored alone against bare. Fading means stronger models get less lift." width="100%" />
</p>

That picture is the **shape** of the output, not a scored run. Your table is the one in `results/`.

<p align="center">
  <a href="https://youngmoneyinvestments.github.io/context-bench/watch.html">
    <img src="docs/assets/film-poster.jpg" alt="Play the 51s film: Boris Cherny, then skills and hooks on Claude, Codex, and Grok" width="100%" />
  </a>
</p>

GitHub’s file viewer will not play this mp4. Watch it here:

**[Play the 51s film](https://youngmoneyinvestments.github.io/context-bench/watch.html)** · [16:9 mp4](https://youngmoneyinvestments.github.io/context-bench/assets/context-bench.mp4) · [9:16](https://youngmoneyinvestments.github.io/context-bench/assets/context-bench-9x16.mp4) · [release](https://github.com/YoungMoneyInvestments/context-bench/releases/tag/film)

## More commands

```bash
# 30-second live smoke (needs a logged-in `claude` CLI)
python3 -m contextbench.cli --smoke

# One class family, one model
python3 -m contextbench.cli --context-dir ~/.claude --split families --models opus

# One skill at a time (slash-invokes the real skill — not a SKILL.md dump)
python3 -m contextbench.cli --context-dir ~/.claude/skills/caveman --harness skill --models haiku

# Subscription CLIs, no API keys
python3 -m contextbench.cli --models sonnet,haiku,grok,codex,cursor,gemini --smoke
```

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
| `--harness auto` | Default. Skill dirs (`SKILL.md`) use slash-invoke; prose dirs use wrap. |
| `--harness skill` | Force slash-invoke (`claude -p /skillname`). Bare arm gets `--disable-slash-commands`. |
| `--harness notes` | Always dump markdown as extra system text (old behavior). |
| `--models opus,sonnet,haiku` | Also: `grok`, `codex`, `cursor`, `gemini`, or `provider:model-id`. |
| `--demo` | Offline mock run. No OAuth, no API keys, no network. Writes `results/dashboard.html`. |
| `--smoke` | First Case × first model. Use this before a 6×3×N burn. |

## Read the numbers honestly

The judge is a model call, not ground truth. Read a few `results/judged_*.json` reasons before trusting a delta. Ten Cases is a smoke bench, not a statistically powered one. If a Profile swings on 1–2 Cases, that is noise.

**Skill dirs use real Claude Code slash-invoke by default** (`--harness auto` / `--harness skill`): `claude -p /skillname` with the Case as the rest of the prompt ([ADR 0004](./docs/adr/0004-fair-cli-wrapping.md)). Prose bundles (`CLAUDE.md`, `examples/context`) still wrap as system context. `--harness notes` forces the old dump.

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

Anthropic deleted ~80% of Claude Code's own system prompt when Opus 5 shipped. The model got better. Boris Cherny's follow-up: do the same thing to *your* stack every six months, then add back only what you watch fail. [Nate Herk's video](https://youtu.be/XNQBCRcwXV4) is what made that advice circulate.

A whole-home REMOVE is not actionable. "hooks are fading on Opus, skills still pay on Haiku" is.

Source clips in the film: [Boris at YC Startup School](https://www.youtube.com/watch?v=qyPCVqFUyDo) · [Nate Herk](https://youtu.be/XNQBCRcwXV4). Short attributed excerpts; the rest is this project's explainer.

## License

MIT
