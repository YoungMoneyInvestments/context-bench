"""Render a local HTML dashboard from a leaderboard markdown + optional judged JSON."""
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path


def _parse_md_tables(md: str) -> list[tuple[str, list[str], list[list[str]]]]:
    """Return [(section_title, headers, rows), ...] for markdown pipe tables."""
    sections: list[tuple[str, list[str], list[list[str]]]] = []
    current_title = "Leaderboard"
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("## "):
            current_title = line[3:].strip()
            i += 1
            continue
        if line.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s\-:|]+\|$", lines[i + 1]):
            headers = [c.strip() for c in line.strip("|").split("|")]
            i += 2
            rows: list[list[str]] = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip("|").split("|")])
                i += 1
            sections.append((current_title, headers, rows))
            continue
        i += 1
    return sections


def _cell_class(text: str) -> str:
    t = text.upper()
    if "KEEP" in t or "✅" in text:
        return "keep"
    if "REMOVE" in t or "❌" in text:
        return "remove"
    if "PROMPT_BLOAT" in t or "🧹" in text:
        return "bloat"
    if text.startswith("+"):
        return "pos"
    if text.startswith("-") and re.match(r"^-\d", text):
        return "neg"
    return ""


def render_html(md: str, *, title: str, source: str) -> str:
    sections = _parse_md_tables(md)
    parts = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8" />',
        '<meta name="viewport" content="width=device-width, initial-scale=1" />',
        f"<title>{html.escape(title)}</title>",
        "<style>",
        ":root { --bg:#0f1218; --panel:#171c25; --ink:#e8edf5; --muted:#8b95a8;",
        "  --line:#2a3344; --keep:#1f6f4a; --bloat:#8a6a1f; --remove:#8b2e2e;",
        "  --pos:#3d9b6e; --neg:#c45c5c; --accent:#6aa6ff; }",
        "* { box-sizing: border-box; }",
        "body { margin:0; font:15px/1.45 ui-sans-serif, system-ui, -apple-system, sans-serif;",
        "  background: radial-gradient(1200px 600px at 10% -10%, #1a2740 0%, var(--bg) 55%);",
        "  color: var(--ink); min-height: 100vh; }",
        "header { padding: 28px 32px 8px; }",
        "h1 { margin:0 0 6px; font-size: 28px; letter-spacing: -0.02em; }",
        "header p { margin:0; color: var(--muted); }",
        "main { padding: 16px 32px 48px; display:grid; gap:22px; }",
        "section { background: color-mix(in srgb, var(--panel) 92%, black);",
        "  border:1px solid var(--line); border-radius: 14px; overflow:hidden; }",
        "section h2 { margin:0; padding:14px 18px; font-size:15px; font-weight:600;",
        "  border-bottom:1px solid var(--line); color:#c9d4e8; }",
        ".wrap { overflow:auto; }",
        "table { width:100%; border-collapse: collapse; min-width: 640px; }",
        "th, td { text-align:left; padding:10px 14px; border-bottom:1px solid var(--line);",
        "  vertical-align: top; font-variant-numeric: tabular-nums; }",
        "th { color: var(--muted); font-size:12px; text-transform: uppercase;",
        "  letter-spacing: 0.04em; font-weight:600; }",
        "tr:last-child td { border-bottom:0; }",
        "code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size:12.5px; }",
        ".keep { color: #7ddea8; }",
        ".bloat { color: #e2c35a; }",
        ".remove { color: #f0a0a0; }",
        ".pos { color: var(--pos); }",
        ".neg { color: var(--neg); }",
        "footer { padding: 0 32px 28px; color: var(--muted); font-size: 12px; }",
        "a { color: var(--accent); }",
        "</style>",
        "</head>",
        "<body>",
        "<header>",
        f"<h1>{html.escape(title)}</h1>",
        f"<p>Source: <code>{html.escape(source)}</code></p>",
        "</header>",
        "<main>",
    ]
    if not sections:
        parts.append("<section><h2>No tables found</h2><div class='wrap'><p style='padding:16px'>Empty leaderboard.</p></div></section>")
    for sec_title, headers, rows in sections:
        parts.append("<section>")
        parts.append(f"<h2>{html.escape(sec_title)}</h2>")
        parts.append('<div class="wrap"><table><thead><tr>')
        for h in headers:
            parts.append(f"<th>{html.escape(h.replace('`', ''))}</th>")
        parts.append("</tr></thead><tbody>")
        for row in rows:
            parts.append("<tr>")
            for cell in row:
                cls = _cell_class(cell)
                shown = html.escape(cell.replace("**", "").replace("`", ""))
                parts.append(f'<td class="{cls}">{shown}</td>')
            parts.append("</tr>")
        parts.append("</tbody></table></div></section>")
    parts.extend(
        [
            "</main>",
            "<footer>context-bench local dashboard — refresh after a run finishes.</footer>",
            "</body></html>",
        ]
    )
    return "\n".join(parts)


def write_dashboard(leaderboard_path: Path, out_path: Path) -> Path:
    md = leaderboard_path.read_text()
    html_doc = render_html(
        md,
        title="context-bench",
        source=str(leaderboard_path),
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_doc)
    meta = {
        "leaderboard": str(leaderboard_path),
        "dashboard": str(out_path),
    }
    out_path.with_suffix(".json").write_text(json.dumps(meta, indent=2) + "\n")
    return out_path


def main() -> None:
    p = argparse.ArgumentParser(description="Render context-bench HTML dashboard")
    p.add_argument("--leaderboard", default=None, help="Path to leaderboard_*.md")
    p.add_argument("--results-dir", default="results")
    p.add_argument("--out", default="results/dashboard.html")
    args = p.parse_args()

    if args.leaderboard:
        board = Path(args.leaderboard)
    else:
        boards = sorted(Path(args.results_dir).glob("leaderboard_*.md"))
        if not boards:
            raise SystemExit(f"no leaderboards in {args.results_dir}")
        board = boards[-1]
    out = write_dashboard(board, Path(args.out))
    print(out)


if __name__ == "__main__":
    main()
