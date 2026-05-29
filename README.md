# LinkedIn Job Applier

CLI tool to automate LinkedIn Easy Apply and Workday applications.

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
# Edit .env with your credentials
```

## Usage

```bash
# Search and apply by keywords
python main.py apply --keywords "Engineering Manager" --location "Bengaluru, India"

# Apply to specific job IDs
python main.py apply --job-ids 1234567890,9876543210

# Apply to Easy Apply only (default), Workday only, or both
python main.py apply -k "Staff Engineer" -t easy_apply
python main.py apply -k "Staff Engineer" -t workday
python main.py apply -k "Staff Engineer" -t both

# Headless mode
python main.py apply -k "Engineering Manager" --headless

# View applied jobs
python main.py status

# Save a value to memory (won't ask again)
python main.py remember notice_period 60
python main.py remember current_ctc 7000000
```

## Environment Variables

```
LINKEDIN_EMAIL=your@email.com
LINKEDIN_PASSWORD=yourpassword
RESUME_PATH=/path/to/resume.pdf
```

Or pass directly: `--email`, `--password`, `--resume`

## Features

- **Easy Apply**: Handles multi-step LinkedIn Easy Apply modal — fills all fields, uploads resume, submits
- **Workday**: Navigates Workday ATS forms, creates account if needed, uploads resume
- **Smart Q&A memory**: Asks unknown questions once, saves answers to `data/memory.json`, never asks again
- **Applied tracker**: Logs all applications to `data/applied_jobs.csv` — skips already-applied jobs
- **Third-party links**: Saves external ATS links to `data/third_party_sites.txt` for manual follow-up
- **Director filter**: Auto-skips Director/VP/CTO/Head-of roles

## Memory Keys

Pre-populated defaults (edit `data/memory.json` or use `remember` command):

| Key | Default |
|-----|---------|
| first_name | Subrahmanya |
| last_name | Bhat |
| phone | 9480420288 |
| city | Bengaluru |
| notice_period | 30 |
| years_experience | 10 |
| current_ctc | 6000000 |
| expected_ctc | 6500000 |
| authorized_to_work | Yes |
| requires_visa_sponsorship | No |

## Data Files

- `data/applied_jobs.csv` — application log
- `data/third_party_sites.txt` — external ATS links
- `data/memory.json` — saved answers and profile data

All data files are gitignored.
