# context-bench

Does your CLAUDE.md/skill/system prompt actually make the model's output *better* — or does it
just make the model quieter about doing what it would have done anyway?

Inspired by [Boris Cherny's](https://github.com/anthropics/claude-code) advice in a recent Y
Combinator interview: *"every 6 months, delete your CLAUDE.md, delete your skills, delete your
hooks — see what the model does, it might surprise you."* This repo turns that advice into a
repeatable check instead of a one-off vibe test.

## What it does

Runs a fixed set of **Cases** (prompt + grading rubric) against a matrix of **Profiles** — every
combination of {model} × {your context bundle vs. no context bundle at all} — then has a
separate judge model score every response against that Case's rubric, blind to which Profile
produced it. Output is a leaderboard: which Profiles actually score higher, and by how much.

```
Case × Profile → Run  (raw output)
Run × Judge    → Judgment  (1-10 score + reasoning)
Judgments      → Leaderboard  (mean score per Profile)
```

Full vocabulary: [`CONTEXT.md`](./CONTEXT.md).

## Why "bare vs. your context bundle," not "on vs. off per skill"

v1 tests exactly the experiment in the video: full context bundle vs. nothing. It does **not**
yet isolate individual skills/hooks/MCP tools from each other — that requires actually invoking
a harness (Claude Code, an agent SDK loop) rather than a single raw API call, which is real
future work, not a corner cut silently. See [issues](../../issues) for status.

## Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .

export ANTHROPIC_API_KEY=...   # required — used for Claude Profiles and as the default judge
export XAI_API_KEY=...         # optional — enables Grok Profiles

python3 -m contextbench.cli
```

Results land in `results/runs_<ts>.json`, `results/judged_<ts>.json`, and a rendered
`results/leaderboard_<ts>.md`.

## Testing your own CLAUDE.md/skills, not the demo bundle

`examples/context/` is a synthetic demo bundle (fictional "Acme Labs" persona) — never your real
config; see [ADR 0001](./docs/adr/0001-context-bundles-are-pointers-not-committed-files.md) for
why. To benchmark your actual setup, edit `contextbench/profiles.py` and point a Profile's
`context_dir` at your own local directory (e.g. `~/.claude`) instead of `examples/context` — it's
never committed, since it's outside this repo.

## Adding your own Cases

Drop a YAML file in `cases/`:

```yaml
category: coding
prompt: |
  <the task>
rubric:
  - <criterion the judge should check>
  - <another criterion>
```

## Reading the leaderboard honestly

The judge is itself a model call, not ground truth — treat scores as a signal to spot-check, not
a verdict to cite blind. Read a few of the underlying `results/judged_*.json` reasoning strings
before trusting a leaderboard delta. If a Profile's score swings on 1-2 Cases, that's noise, not
a finding — the rubric-graded Cases here are a starting set of 6, not a statistically powered
benchmark.

## License

MIT
