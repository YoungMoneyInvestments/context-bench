# ADR 0002: Testing via OmniRoute OAuth Subscriptions & Harness Realities

## Status
Accepted — **Superseded in practice by direct CLI harness (`claude` / `grok` / `codex` OAuth adapters); OmniRoute optional/fallback only.**

## Context
1. **User Goal**: The user (Cameron) explicitly wants to run model comparisons using his existing **subscriptions / OAuth accounts** (Claude Team/Pro OAuth, Grok/xAI OAuth, Codex/Cursor/Antigravity OAuth pools stored in OmniRoute), **NOT API key pay-per-token credits**.
2. **Goal of the Benchmark**: Benchmark how a user's *local environment* (their active `CLAUDE.md`, custom skills, hooks, and MCP tools) affects output quality on specific tasks compared to a "bare" baseline without those instructions/tools.
3. **The Architectural Conflict**:
   - Direct provider API calls (`anthropic.Anthropic()`, `openai.OpenAI()`) require paid API keys (`sk-...`) per token. They bypass all local CLI hooks, system prompts, skills, and OAuth session tokens.
   - Calling raw LLM APIs with system prompts tests static prompt engineering, but it does **not** exercise live CLI harness behaviors (such as dynamic tool calls, skill dispatches, or hook overrides).
   - OmniRoute holds Cameron's active pool of OAuth subscriptions (`claude`, `grok-cli`, `xai-oauth`, `codex`, `antigravity`, `agy`, etc.) so requests run under subscription entitlement rather than direct API key billing.

## Decision
1. **Add OmniRoute as the Default Provider Adapter** in `context-bench`.
   - Instead of requiring direct `ANTHROPIC_API_KEY` or `XAI_API_KEY` environment variables, `context-bench` will route requests through OmniRoute MCP / local proxy endpoints.
   - This routes requests through Cameron's authenticated OAuth subscription pools (`claude`, `grok-cli`, `xai-oauth`, etc.).
2. **Acknowledge the Layer Distinction**:
   - **Layer A (Prompt/Context Benchmarking via OmniRoute)**: Tests how adding markdown context/instructions to a model request via OmniRoute OAuth changes output quality vs. bare prompts.
   - **Layer B (Live Harness Benchmarking)**: To test interactive CLI skills/hooks/MCPs (e.g. Claude Code or Hermes execution), `context-bench` can optionally invoke the CLI binary (`claude --print` or subagent runner) directly in a temporary workspace with or without `~/.claude/CLAUDE.md` and `~/.claude/skills/`.

## Consequences
- **No API key spend needed**: Uses existing subscription logins stored in OmniRoute.
- **True reflection of actual usage**: Matches how Cameron actually codes (routing through OmniRoute and OAuth models).
