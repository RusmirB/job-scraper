"""Write matches to a CSV and a self-contained HTML report."""
from __future__ import annotations

import csv
import html
from datetime import datetime
from pathlib import Path

from .models import Job


def write_csv(jobs: list[Job], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            ["score", "title", "company", "salary", "location", "source", "posted", "url", "why"]
        )
        for job in jobs:
            writer.writerow(
                [
                    job.score,
                    job.title,
                    job.company,
                    job.salary,
                    job.location,
                    job.source,
                    job.posted.date().isoformat() if job.posted else "",
                    job.url,
                    "; ".join(job.reasons),
                ]
            )


def _row(job: Job) -> str:
    reasons = " ".join(
        f'<span class="tag {"neg" if r.startswith("-") else "pos"}">{html.escape(r)}</span>'
        for r in job.reasons
    )
    posted = job.posted.date().isoformat() if job.posted else "—"
    salary = (
        f'<span class="salary">💰 {html.escape(job.salary)}</span>'
        if job.salary
        else '<span class="nosal">salary n/a</span>'
    )
    return f"""
    <tr>
      <td class="score">{job.score}</td>
      <td>
        <a href="{html.escape(job.url)}" target="_blank">{html.escape(job.title)}</a> {salary}
        <div class="meta">{html.escape(job.company)} · {html.escape(job.location or "Remote")} ·
          <span class="src">{html.escape(job.source)}</span> · {posted}</div>
        <div class="reasons">{reasons}</div>
      </td>
    </tr>"""


def write_html(jobs: list[Job], path: str) -> None:
    rows = "".join(_row(j) for j in jobs)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>QA Job Matches</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{ font: 15px/1.5 system-ui, sans-serif; margin: 0; background: Canvas; color: CanvasText; }}
  header {{ padding: 20px 24px; border-bottom: 1px solid #8884; }}
  h1 {{ margin: 0; font-size: 20px; }}
  .sub {{ opacity: .7; font-size: 13px; }}
  table {{ width: 100%; border-collapse: collapse; }}
  td {{ padding: 14px 24px; border-bottom: 1px solid #8883; vertical-align: top; }}
  .score {{ font-weight: 700; font-size: 18px; width: 56px; color: #16a34a; }}
  a {{ color: #2563eb; text-decoration: none; font-weight: 600; }}
  a:hover {{ text-decoration: underline; }}
  .meta {{ font-size: 13px; opacity: .75; margin-top: 3px; }}
  .src {{ background: #6366f133; padding: 1px 6px; border-radius: 4px; }}
  .salary {{ display: inline-block; background: #16a34a22; color: #16a34a; font-weight: 600;
             font-size: 12px; padding: 1px 8px; border-radius: 10px; margin-left: 6px; }}
  .nosal {{ font-size: 11px; opacity: .45; margin-left: 6px; }}
  .reasons {{ margin-top: 6px; }}
  .tag {{ display: inline-block; font-size: 11px; padding: 1px 6px; margin: 2px 3px 0 0; border-radius: 4px; }}
  .pos {{ background: #16a34a22; color: #16a34a; }}
  .neg {{ background: #dc262622; color: #dc2626; }}
</style></head><body>
<header><h1>QA / SDET Job Matches</h1>
<div class="sub">{len(jobs)} new match(es) · generated {now}</div></header>
<table><tbody>{rows}</tbody></table>
</body></html>"""
    Path(path).write_text(doc, encoding="utf-8")
