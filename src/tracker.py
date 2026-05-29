"""Tracks applied jobs — CSV log + third-party site links file."""
import csv
import os
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
APPLIED_CSV = DATA_DIR / "applied_jobs.csv"
THIRD_PARTY_FILE = DATA_DIR / "third_party_sites.txt"

FIELDNAMES = ["date", "job_id", "title", "company", "location", "url", "apply_type", "status", "notes"]


def _ensure_csv():
    DATA_DIR.mkdir(exist_ok=True)
    if not APPLIED_CSV.exists():
        with open(APPLIED_CSV, "w", newline="") as f:
            csv.DictWriter(f, fieldnames=FIELDNAMES).writeheader()


def already_applied(job_id: str) -> bool:
    _ensure_csv()
    with open(APPLIED_CSV) as f:
        return any(row["job_id"] == str(job_id) for row in csv.DictReader(f))


def log_applied(job_id: str, title: str, company: str, location: str,
                url: str, apply_type: str = "easy_apply", status: str = "submitted", notes: str = ""):
    _ensure_csv()
    with open(APPLIED_CSV, "a", newline="") as f:
        csv.DictWriter(f, fieldnames=FIELDNAMES).writerow({
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "job_id": job_id,
            "title": title,
            "company": company,
            "location": location,
            "url": url,
            "apply_type": apply_type,
            "status": status,
            "notes": notes,
        })
    print(f"  [LOGGED] {company} - {title} ({status})")


def log_third_party(job_id: str, title: str, company: str, ats_url: str, linkedin_url: str):
    DATA_DIR.mkdir(exist_ok=True)
    with open(THIRD_PARTY_FILE, "a") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d')}] {company} | {title}\n")
        f.write(f"  LinkedIn: {linkedin_url}\n")
        f.write(f"  ATS:      {ats_url}\n\n")
    print(f"  [SAVED] Third-party link: {company} - {title}")


def load_applied() -> list[dict]:
    _ensure_csv()
    with open(APPLIED_CSV) as f:
        return list(csv.DictReader(f))
