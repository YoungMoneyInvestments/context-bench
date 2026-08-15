from __future__ import annotations

from pathlib import Path

import yaml

from contextbench.models import Case
from contextbench.paths import resolve_cases_dir


def load_cases(cases_dir: str = "cases") -> list[Case]:
    root = resolve_cases_dir(cases_dir)
    cases = []
    for f in sorted(root.glob("*.yaml")):
        data = yaml.safe_load(f.read_text())
        cases.append(Case(id=f.stem, category=data["category"], prompt=data["prompt"], rubric=data["rubric"]))
    return cases
