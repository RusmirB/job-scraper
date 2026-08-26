# QA / SDET Remote Job Scanner

Scans many remote-job sources every few hours, keeps only QA/SDET/tester roles,
scores them against your stack, drops ones you've already seen, and writes a
ranked **HTML + CSV report** of new matches.

## Sources (Phase 1)

| Source          | Type       | Notes                                  |
|-----------------|------------|----------------------------------------|
| Remotive        | JSON API   | `category=qa`                          |
| Arbeitnow       | JSON API   | paginated                              |
| We Work Remotely| RSS        | programming + devops feeds             |
| RemoteOK        | JSON API   | tags + salary                          |
| Jobicy          | JSON API   | `tag=qa`                               |
| Himalayas       | JSON API   | location restrictions                  |
| RemoteJobs.org  | JSON API   | salary fields                          |
| Hacker News     | JSON API   | monthly "Who is hiring?" thread        |
| Greenhouse      | JSON API   | one board per slug in `companies.yaml` |
| Lever           | JSON API   | one board per slug in `companies.yaml` |
| Ashby           | JSON API   | boards + compensation, `companies.yaml`|
| SmartRecruiters | JSON API   | one company per slug in `companies.yaml`|
| Adzuna          | JSON API   | salary-rich aggregator; needs free key |

> **Adzuna** is opt-in: set `ADZUNA_APP_ID` / `ADZUNA_APP_KEY` (free from
> developer.adzuna.com). Skipped cleanly if unset.
>
> **Not integrated on purpose:** LinkedIn / Indeed / Upwork (auth + anti-bot + ToS —
> use their native saved-search alerts); Google Jobs (no free API — needs paid SerpAPI);
> Workable / Recruitee (public endpoints are now locked/auth-only).

## Configure

- `config/profile.yaml` — required/excluded keywords, scoring weights, `min_score`.
  Everything is data; no code changes needed to tune your matches.
- `config/companies.yaml` — Greenhouse/Lever company slugs to scan directly.

## Run locally

```bash
pip install -r requirements.txt
python main.py            # writes report.html + report.csv
python main.py --all      # include already-seen jobs (first run / testing)
```

Open `report.html` in a browser. `jobs.db` (SQLite) tracks what you've already
been shown so alerts never repeat.

## Run on a schedule (free)

Push to GitHub. `.github/workflows/scan.yml` runs every 4 hours, uploads the
report as a build artifact, and commits `jobs.db` so the "seen" memory persists
between runs. Trigger manually anytime via **Actions → Scan QA jobs → Run workflow**.

## Roadmap

- **Phase 2:** Telegram/email alerts, more company boards (Ashby, Workable, Recruitee).
- **Phase 3:** LLM pass — summarize role, flag geo restrictions, estimate match %,
  draft a tailored cover letter.
