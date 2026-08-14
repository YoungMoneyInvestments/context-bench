from __future__ import annotations

import json
import re
from dataclasses import asdict

from contextbench.models import Case, Judgment, Run
from contextbench.providers import CALLERS

JUDGE_PROMPT = """You are grading a single AI response against a rubric. Be strict and specific.

Task the AI was given:
---
{prompt}
---

Rubric (score 1-10 overall, weighing every point):
{rubric}

AI's response:
---
{output}
---

Reply with ONLY a JSON object: {{"score": <1-10 integer>, "reasoning": "<one sentence>"}}
"""


def judge_run(run: Run, case: Case, judge_provider: str, judge_model: str) -> Judgment:
    rubric_text = "\n".join(f"- {r}" for r in case.rubric)
    prompt = JUDGE_PROMPT.format(prompt=case.prompt, rubric=rubric_text, output=run.output)
    caller = CALLERS[judge_provider]
    text, _, _ = caller(judge_model, "", prompt)
    score, reasoning = _parse_verdict(text)
    return Judgment(case_id=run.case_id, profile_id=run.profile_id, score=score, reasoning=reasoning, judge_model=judge_model)


def _parse_verdict(text: str) -> tuple[int, str]:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return 0, f"unparseable judge output: {text[:200]!r}"
    try:
        data = json.loads(match.group(0))
        return int(data["score"]), str(data["reasoning"])
    except (json.JSONDecodeError, KeyError, ValueError):
        return 0, f"unparseable judge output: {text[:200]!r}"


def judge_all(runs: list[Run], cases_by_id: dict[str, Case], judge_provider: str, judge_model: str) -> list[Judgment]:
    judgments = []
    for run in runs:
        case = cases_by_id[run.case_id]
        print(f"[judge] {run.case_id} x {run.profile_id}")
        judgments.append(judge_run(run, case, judge_provider, judge_model))
    return judgments


def judgments_to_dicts(judgments: list[Judgment]) -> list[dict]:
    return [asdict(j) for j in judgments]
