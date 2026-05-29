# LinkedIn Job Applier

A Python CLI that automates LinkedIn job applications. Opens a real Chrome browser, logs into LinkedIn, searches for jobs, and submits Easy Apply and Workday applications automatically — uploading your resume, filling every form field, and remembering answers to questions it has never seen before.

No API keys. No scraping. Real browser, real clicks.

---

## How it works

```
python main.py apply
       │
       ├─ Opens Chrome (visible window or headless)
       ├─ Logs into LinkedIn (auto or manual login)
       ├─ Searches jobs by keyword + location
       │
       └─ For each job:
           ├─ Already applied? → SKIP
           ├─ Director/VP/CTO/Head-of title? → SKIP
           ├─ Easy Apply job?
           │   ├─ Clicks "Easy Apply"
           │   ├─ Fills name, phone, salary, notice, location, etc.
           │   ├─ Uploads resume PDF
           │   ├─ Answers radio/checkbox/dropdown questions
           │   ├─ Unknown question → asks you ONCE, saves answer forever
           │   └─ Clicks Next → Review → Submit
           ├─ Workday job?
           │   ├─ Navigates to Workday URL
           │   ├─ Creates account if needed
           │   └─ Fills multi-step wizard, submits
           └─ 3rd party ATS (Greenhouse, Lever, Ashby)?
               └─ Saves link to data/third_party_sites.txt for manual apply
```

---

## Requirements

- Python 3.10+
- That's it — everything else installs automatically on first run

**First run auto-installs:**
- Creates a `.venv` virtual environment in the project folder
- Installs `playwright`, `click`, `python-dotenv`
- Downloads Chromium browser

---

## Setup

```bash
git clone https://github.com/subrahmanyabhat/linkedin-job-applier
cd linkedin-job-applier
cp .env.example .env
```

Edit `.env`:
```
LINKEDIN_EMAIL=your@email.com
LINKEDIN_PASSWORD=yourpassword
RESUME_PATH=/path/to/your/resume.pdf
```

Leave `LINKEDIN_PASSWORD` empty to use **manual login** — browser opens, you log in yourself, then press Enter to continue.

---

## Usage

```bash
# Basic — search Engineering Manager jobs in Bengaluru, apply to 5
python main.py apply

# Custom keywords and location
python main.py apply --keywords "Staff Engineer" --location "Hyderabad, India"

# Apply to specific job IDs directly
python main.py apply --job-ids 1234567890,9876543210

# Apply to Easy Apply only (default), Workday only, or both
python main.py apply -t easy_apply
python main.py apply -t workday
python main.py apply -t both

# Control how many jobs to apply to
python main.py apply --limit 20 --max-pages 10

# Run without opening a visible browser window
python main.py apply --headless

# View all submitted applications
python main.py status

# Update a memory value (won't be asked again)
python main.py remember notice_period 60
python main.py remember current_ctc 7500000
python main.py remember years_experience 12
```

### All options

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--keywords` | `-k` | `Engineering Manager` | Job search keywords |
| `--location` | `-l` | `Bengaluru, Karnataka, India` | Job location |
| `--job-ids` | `-j` | — | Comma-separated job IDs, skips search |
| `--max-pages` | `-p` | `5` | Search result pages to scrape |
| `--apply-type` | `-t` | `easy_apply` | `easy_apply`, `workday`, or `both` |
| `--email` | `-e` | from `.env` | LinkedIn email |
| `--password` | `-w` | from `.env` | LinkedIn password (omit for manual login) |
| `--resume` | `-r` | from `.env` | Path to resume PDF |
| `--headless` | | `false` | Hide browser window |
| `--limit` | | `50` | Max applications to submit |

---

## Smart Q&A Memory

The first time the script encounters a question it doesn't know (e.g. "How many years of fintech experience?"), it pauses and asks you:

```
[QUESTION] How many years of fintech experience do you have?
Your answer: 3
Saved. Won't ask again.
```

The answer is stored in `data/memory.json`. Every future run uses it silently.

### Pre-filled defaults

These are answered automatically without ever asking:

| Question type | Answer |
|--------------|--------|
| First name | Subrahmanya |
| Last name | Bhat |
| Phone / mobile | 9480420288 |
| City / location | Bengaluru |
| Notice period | 30 days |
| Years of experience | 10 |
| Current CTC / salary | 60,00,000 |
| Expected CTC / salary | 65,00,000 |
| Authorized to work in India | Yes |
| Requires visa sponsorship | No |
| Cover letter / summary | NA |

Override any default:
```bash
python main.py remember notice_period 45
python main.py remember current_ctc 8000000
```

---

## Tracking

Every application is logged to `data/applied_jobs.csv`:

```
date,job_id,title,company,location,url,apply_type,status,notes
2025-05-29,4408177466,Engineering Manager,Atlassian,Bengaluru,...,easy_apply,submitted,
```

External ATS links saved to `data/third_party_sites.txt`:
```
[2025-05-29] Stripe | Engineering Manager
  LinkedIn: https://www.linkedin.com/jobs/view/4408177466/
  Apply at: https://stripe.com/jobs/listing/...
```

All data files are gitignored — never committed to GitHub.

---

## Project structure

```
linkedin-job-applier/
├── main.py                  # CLI entry point (Click commands)
├── src/
│   ├── browser.py           # Playwright browser setup + LinkedIn login
│   ├── scraper.py           # Job search + job detail scraper
│   ├── easy_apply.py        # LinkedIn Easy Apply modal handler
│   ├── workday.py           # Workday ATS handler
│   ├── memory.py            # Q&A memory + profile defaults
│   └── tracker.py           # Applied jobs CSV + third-party links
├── data/                    # Runtime data (gitignored)
│   ├── applied_jobs.csv
│   ├── memory.json
│   └── third_party_sites.txt
├── .env                     # Your credentials (gitignored)
├── .env.example             # Template
└── requirements.txt
```

---

## Related

- [linkedin-apply-skill](https://github.com/subrahmanyabhat/linkedin-apply-skill) — Claude Code AI skill version: uses Claude's intelligence + Playwright MCP to handle any form, fix errors live, and reason about unknown questions.
