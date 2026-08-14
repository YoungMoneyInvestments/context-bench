"""Thin per-provider callers. Returns (text, input_tokens, output_tokens).

Supports:
1. Local CLI harness execution (`claude -p`, `codex exec`, `grok --single`) using your
   active local OAuth/subscription sessions — no API key needed.
2. Direct API keys (`anthropic`, `openai`, `xai`) if configured.
3. OmniRoute proxy fallback if explicitly configured.

Gemini and Cursor are not wired in: `gemini` CLI is installed but has never completed its
interactive browser OAuth login (verified live — a headless call hung on the auth prompt);
`c‍ursor-agent` isn't installed at all. See gaps-inbox / repo issues for status.
"""
from __future__ import annotations

import os
import subprocess
import tempfile

# Run claude -p from a neutral scratch cwd, not this repo: inside the repo, ambient
# hooks/CLAUDE.md surface this repo's own git status ("uncommitted change in profiles.py...")
# and the model answers *that* instead of doing the Case. Reused across calls (cheap, no
# per-run mkdtemp cost) since it's never written to.
_NEUTRAL_CWD = tempfile.mkdtemp(prefix="contextbench-cwd-")


def _cli_model_flag(model: str) -> list[str]:
    if "sonnet" in model:
        return ["--model", "claude-sonnet-5"]
    if "haiku" in model:
        return ["--model", "claude-haiku-4-5-20251001"]
    if "opus" in model:
        return ["--model", "claude-opus-5"]
    return []


def call_cli_harness(model: str, system: str, prompt: str) -> tuple[str, int, int]:
    """Execute via the local `claude -p` CLI using the active OAuth subscription.

    Context notes go through `--system-prompt-file` (real system role), not concatenated
    into the user turn as "System Instructions:". That old wrapping made Opus/Sonnet
    treat SKILL.md dumps as injection or help-text (issue #1).
    """
    sys_path = None
    cmd = ["claude", "-p", prompt, *_cli_model_flag(model)]
    if system:
        fd, sys_path = tempfile.mkstemp(prefix="contextbench-sys-", suffix=".txt")
        with os.fdopen(fd, "w") as handle:
            handle.write(system)
        cmd.extend(["--system-prompt-file", sys_path])

    try:
        res = subprocess.run(
            cmd, capture_output=True, text=True, timeout=180, check=True, cwd=_NEUTRAL_CWD
        )
        text = res.stdout.strip()
        in_tok = (len(prompt.split()) + len(system.split())) * 2
        out_tok = len(text.split()) * 2
        return text, in_tok, out_tok
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or "") + (e.stdout or "")
        if sys_path and "system-prompt-file" in stderr.lower():
            # Older CLI builds only have --system-prompt. Fall back; ARG_MAX is the risk.
            cmd = ["claude", "-p", prompt, "--system-prompt", system, *_cli_model_flag(model)]
            res = subprocess.run(
                cmd, capture_output=True, text=True, timeout=180, check=True, cwd=_NEUTRAL_CWD
            )
            text = res.stdout.strip()
            in_tok = (len(prompt.split()) + len(system.split())) * 2
            out_tok = len(text.split()) * 2
            return text, in_tok, out_tok
        raise RuntimeError(f"CLI harness execution failed: {e}") from e
    except Exception as e:
        raise RuntimeError(f"CLI harness execution failed: {e}") from e
    finally:
        if sys_path:
            try:
                os.unlink(sys_path)
            except OSError:
                pass


def call_grok_cli(model: str, system: str, prompt: str) -> tuple[str, int, int]:
    """Execute via the local `grok` CLI (own OAuth/session, independent of XAI_API_KEY —
    verified live: XAI_API_KEY was credit-exhausted but this path still worked).

    `grok --single` has no real system-role flag, so `system` is concatenated as plain
    text ahead of the task. It is NOT relabeled "System Instructions:" — the caller
    (wrap_request) already picked the framing for the active --wrap mode (e.g. fair mode's
    "optional reference" preamble); slapping our own "System Instructions:" label back on
    top would silently reproduce the raw-mode wrapping bug from issue #1 for this provider
    only, regardless of which --wrap mode was requested.
    """
    full_prompt = f"{system}\n\n{prompt}" if system else prompt
    cmd = ["grok", "--single", full_prompt, "--model", model, "--cwd", _NEUTRAL_CWD]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=180, check=True)
        text = res.stdout.strip()
        in_tok = len(full_prompt.split()) * 2
        out_tok = len(text.split()) * 2
        return text, in_tok, out_tok
    except Exception as e:
        raise RuntimeError(f"grok CLI execution failed: {e}") from e


def call_codex_cli(model: str, system: str, prompt: str) -> tuple[str, int, int]:
    """Execute via the local `codex exec` CLI (own ChatGPT/OAuth session).

    Runs from the same neutral cwd as the Claude harness: codex loads this repo's own
    project hooks/skills/MCP config otherwise, burning tens of thousands of tokens on
    ambient noise instead of the Case (verified live: a trivial "pong" prompt run from
    this repo cost 27.5k tokens before this fix). `--output-last-message` isolates the
    final answer from interleaved hook/MCP log lines that otherwise pollute stdout.

    `codex exec` has no system-role flag either, so `system` is concatenated as plain
    text, not relabeled "System Instructions:" — same reasoning as call_grok_cli.
    """
    full_prompt = f"{system}\n\n{prompt}" if system else prompt
    fd, out_path = tempfile.mkstemp(prefix="contextbench-codex-out-", suffix=".txt")
    os.close(fd)
    cmd = [
        "codex", "exec",
        "-C", _NEUTRAL_CWD,
        "--skip-git-repo-check",
        "--model", model,
        "--output-last-message", out_path,
        full_prompt,
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=180, check=True)
        with open(out_path) as f:
            text = f.read().strip()
        in_tok = len(full_prompt.split()) * 2
        out_tok = len(text.split()) * 2
        return text, in_tok, out_tok
    except Exception as e:
        raise RuntimeError(f"codex CLI execution failed: {e}") from e
    finally:
        try:
            os.unlink(out_path)
        except OSError:
            pass


def call_omniroute(model: str, system: str, prompt: str) -> tuple[str, int, int]:
    import json
    import urllib.request

    omni_url = os.environ.get("OMNIROUTE_URL", "http://127.0.0.1:18800/v1/chat/completions")
    omni_key = os.environ.get("OMNIROUTE_API_KEY", "sk-omniroute-local")

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 2048,
    }

    req = urllib.request.Request(
        omni_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {omni_key}",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        res_data = json.loads(resp.read().decode("utf-8"))

    choices = res_data.get("choices", [])
    text = choices[0]["message"]["content"] if choices else ""
    usage = res_data.get("usage", {})
    in_tok = usage.get("prompt_tokens", 0)
    out_tok = usage.get("completion_tokens", 0)

    return text, in_tok, out_tok


def call_anthropic(model: str, system: str, prompt: str) -> tuple[str, int, int]:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return call_cli_harness(model, system, prompt)

    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    resp = client.messages.create(
        model=model,
        max_tokens=2048,
        system=system if system else None,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text")
    return text, resp.usage.input_tokens, resp.usage.output_tokens


def call_xai(model: str, system: str, prompt: str) -> tuple[str, int, int]:
    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        return call_cli_harness(model, system, prompt)

    return _call_openai_compatible(
        base_url="https://api.x.ai/v1",
        api_key=api_key,
        model=model,
        system=system,
        prompt=prompt,
    )


def call_openai(model: str, system: str, prompt: str) -> tuple[str, int, int]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return call_cli_harness(model, system, prompt)

    return _call_openai_compatible(
        base_url="https://api.openai.com/v1",
        api_key=api_key,
        model=model,
        system=system,
        prompt=prompt,
    )


def _call_openai_compatible(
    *, base_url: str, api_key: str, model: str, system: str, prompt: str
) -> tuple[str, int, int]:
    from openai import OpenAI

    client = OpenAI(base_url=base_url, api_key=api_key)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    resp = client.chat.completions.create(model=model, messages=messages, max_tokens=2048)
    text = resp.choices[0].message.content or ""
    usage = resp.usage
    in_tok = usage.prompt_tokens if usage else 0
    out_tok = usage.completion_tokens if usage else 0
    return text, in_tok, out_tok


CALLERS = {
    "anthropic": call_anthropic,
    "xai": call_xai,
    "openai": call_openai,
    "omniroute": call_omniroute,
    "cli": call_cli_harness,
    "grok": call_grok_cli,
    "codex": call_codex_cli,
}
