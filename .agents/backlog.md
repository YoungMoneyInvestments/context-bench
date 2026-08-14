# context-bench backlog

## Open

- [ ] Class split is markdown-as-notes, not live hook/skill invocation — same limit as ADR 0004
- [ ] Hooks with no markdown are name-inventories only; executing hooks is future work

- [ ] Gemini CLI OAuth login (interactive, one-time) then wire `call_gemini_cli` — issue #2
- [ ] Real skill-invocation harness (not system-prompt dump) — issue #1
- [ ] Direct xAI/OpenAI API key path still broken (CLI OAuth workaround shipped) — issue #3
- [ ] Multi-model full run (sonnet/haiku/grok/codex × 10 cases) — kicked off 2026-08-14; watch `/tmp/contextbench-multi-20260814.log` (may be buffered) and `results/leaderboard_*.md`
- [ ] Optional: commit Elo + 4 new cases + cursor provider when Cameron asks

## Done 2026-08-14

- [x] Arena-style Elo + bootstrap CI on leaderboard
- [x] Cases 07–10 (review/boundary/plan/ambiguity)
- [x] cursor-agent provider (`--models cursor`) via subscription OAuth
- [x] ADR 0002 note: CLI OAuth preferred; OmniRoute optional
