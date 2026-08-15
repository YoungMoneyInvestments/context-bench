# Isolated `bare` uses `--safe-mode`

Older Claude CLI builds had no way to keep OAuth and also skip ambient `~/.claude`
customizations. `--bare` / `CLAUDE_CODE_SIMPLE=1` dropped keychain login. That made a
true empty baseline look impossible, so an earlier note claimed ambient config
"cancels out" of the delta. It does not: class arms were being added *on top of*
the same loaded home, so the bench was not scoring each class alone.

Current `claude -p` exposes `--safe-mode`: CLAUDE.md, skills, hooks, plugins, MCP,
and custom agents stay off; auth and model selection still work. context-bench now
passes `--safe-mode` on every Claude CLI arm.

- **bare** = `--safe-mode` and no extra system text.
- **treatment** = `--safe-mode` plus only the selected files, attached through
  `--system-prompt-file`.

That is a static wrap of the selected markdown. It is not a live skill/hook/plugin
execution test. `--harness skill` still requires a `SKILL.md` directory so you can
point at one skill, but the measurement is the file text, not `/{skill}`.

Absolute scores can be compared across machines that share the same cases and
isolated flags. Deltas remain within-run paired per-case differences.
