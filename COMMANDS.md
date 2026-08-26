# Useful Commands

Quick reference for running and tuning the QA job scanner.
Run everything from the project folder: `cd c:\job-scraper`

---

## Run the scanner

```powershell
python main.py              # scan everything, report only NEW jobs (not seen before)
python main.py --all        # scan everything, report ALL matches (ignore "seen" memory)
```

Outputs: `report.html` (open in browser) and `report.csv` (open in Excel).
Both are ordered **newest posting day first**, and within the same day the highest
score comes first. Jobs whose source gives no date land at the bottom.

```powershell
start report.html           # open the HTML report in your default browser
Invoke-Item report.csv      # open the CSV in Excel
```

---

## First-time setup (only once)

```powershell
python -m pip install -r requirements.txt
```

---

## Understand the two layers

- **Aggregators** (Remotive, Arbeitnow, WWR, RemoteOK, Jobicy, Himalayas) scan the
  **entire remote job market** — thousands of companies, including tiny ones hiring
  their first QA. This is always on. No config needed.
- **`config/companies.yaml`** only ADDS specific companies whose jobs live only on
  their own Greenhouse/Lever page. Empty it and you still scan the whole market.

---

## Tune what counts as a match

Edit `config/profile.yaml`, then just re-run `python main.py --all`.

- `required_any` — a job is dropped unless it contains at least one of these words.
  Make it **stricter** (fewer false positives like DevOps roles) by trimming broad
  words. Make it **looser** (more results) by adding words.
- `excluded` — drop jobs containing any of these (e.g. `us citizens only`, `internship`).
- `weights` — points per keyword. Raise the ones matching your strengths (playwright,
  python, sql, etl...).
- `min_score` — only jobs at/above this score reach the report. Raise it to see fewer,
  stronger matches; lower it to see more.

---

## Enable Adzuna (salary-rich aggregator, optional)

Adzuna needs a free key from https://developer.adzuna.com/ . Once you have the
app_id and app_key, set them for the session, then run:

```powershell
$env:ADZUNA_APP_ID  = "your_app_id"
$env:ADZUNA_APP_KEY = "your_app_key"
python main.py --all
```

Without the keys, Adzuna is skipped cleanly (every other source still runs).
On GitHub Actions, add them as repo **Secrets** and pass them as `env:` in the workflow.

---

## Add companies to the bonus layer (optional)

Edit `config/companies.yaml`. Find the slug in a company's careers URL:

```
https://boards.greenhouse.io/gitlab   ->  greenhouse:  - gitlab
https://jobs.lever.co/netflix         ->  lever:       - netflix
```

A wrong/dead slug just prints a warning and is skipped — it never breaks the run.

---

## Reset the "seen" memory

`jobs.db` remembers every job already shown so you're not alerted twice.
To start fresh (everything counts as new again):

```powershell
Remove-Item jobs.db
```

---

## Test a single source (debug)

```powershell
python -c "from scanner.sources import remotive; print(len(remotive.fetch()), 'jobs')"
python -c "from scanner.sources import remoteok; print(len(remoteok.fetch()), 'jobs')"
```

---

## Put it on autopilot (GitHub Actions)

```powershell
git init
git add .
git commit -m "QA job scanner"
# create a repo on github.com, then:
git remote add origin https://github.com/<you>/<repo>.git
git push -u origin main
```

Then on GitHub: **Actions -> Scan QA jobs -> Run workflow** to test it.
It auto-runs every 4 hours after that.
