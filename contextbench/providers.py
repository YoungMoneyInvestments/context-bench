"""Thin per-provider callers. Returns (text, input_tokens, output_tokens).

Supports:
1. Local CLI harness execution (`claude -p`) using your active local OAuth subscriptions.
2. Direct API keys (`anthropic`, `openai`, `xai`) if configured.
3. OmniRoute proxy fallback if explicitly configured.
"""
from __future__ import annotations

import os
import subprocess
import time


def call_cli_harness(model: str, system: str, prompt: str) -> tuple[str, int, int]:
    """Execute via the local `claude -p` CLI binary using your active local subscription.
    Handles bare vs context-bundle prompts naturally.
    """
    full_prompt = prompt
    if system:
        full_prompt = f"System Instructions:\n{system}\n\nTask:\n{prompt}"

    cmd = ["claude", "-p", full_prompt]

    # Map model flags if needed
    if "sonnet" in model:
        cmd.extend(["--model", "claude-sonnet-5"])
    elif "haiku" in model:
        cmd.extend(["--model", "claude-haiku-4-5-20251001"])
    elif "opus" in model:
        cmd.extend(["--model", "claude-opus-5"])

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=True)
        text = res.stdout.strip()
        # Rough token estimation for local CLI execution
        in_tok = len(full_prompt.split()) * 2
        out_tok = len(text.split()) * 2
        return text, in_tok, out_tok
    except Exception as e:
        raise RuntimeError(f"CLI harness execution failed: {e}") from e


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
}
