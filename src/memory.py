"""Persistent Q&A memory — stores user answers, never asks twice."""
import json
import os
from pathlib import Path

MEMORY_FILE = Path(__file__).parent.parent / "data" / "memory.json"

_DEFAULTS = {
    "first_name": "Subrahmanya",
    "last_name": "Bhat",
    "full_name": "Subrahmanya Bhat",
    "email": "",
    "phone": "9480420288",
    "phone_country": "India (+91)",
    "location": "Bengaluru, Karnataka, India",
    "city": "Bengaluru",
    "state": "Karnataka",
    "country": "India",
    "zip": "560066",
    "linkedin_url": "https://www.linkedin.com/in/subbusbhat",
    "current_company": "BrowserStack",
    "current_title": "Engineering Manager",
    "years_experience": "10",
    "current_ctc": "6000000",
    "expected_ctc": "6500000",
    "notice_period": "30",
    "authorized_to_work": "Yes",
    "requires_visa_sponsorship": "No",
    "worked_here_before": "No",
    "has_family_at_company": "No",
    "has_outside_business": "No",
    "willing_to_relocate": "Yes",
    "willing_to_work_onsite": "Yes",
    "gender": "Male",
    "ethnicity": "Asian",
    "veteran_status": "I am not a protected veteran",
    "disability_status": "I don't wish to answer",
    "headline": "Engineering Manager | 10+ yrs | Node.js, Go, React | Building High-Ownership Teams",
    "cover_letter": "NA",
    "salary_expectation": "6500000",
    "resume_path": "",
}


def load() -> dict:
    MEMORY_FILE.parent.mkdir(exist_ok=True)
    if MEMORY_FILE.exists():
        data = json.loads(MEMORY_FILE.read_text())
        # Merge with defaults for any missing keys
        return {**_DEFAULTS, **data}
    return dict(_DEFAULTS)


def save(data: dict):
    MEMORY_FILE.parent.mkdir(exist_ok=True)
    MEMORY_FILE.write_text(json.dumps(data, indent=2))


def get(key: str, prompt: str | None = None) -> str:
    """Get value by key. If missing, prompt user, save, return."""
    data = load()
    if data.get(key):
        return data[key]
    if prompt is None:
        return ""
    val = input(f"{prompt}: ").strip()
    if val:
        data[key] = val
        save(data)
    return val


def set_value(key: str, value: str):
    data = load()
    data[key] = value
    save(data)


def answer_question(question: str, options: list[str] | None = None) -> str:
    """
    Try to auto-answer a question from memory.
    Falls back to asking user if unknown; saves answer.
    """
    data = load()
    q_lower = question.lower()

    # Rule-based matching
    if any(k in q_lower for k in ["legally authorized", "authorized to work", "right to work"]):
        return data.get("authorized_to_work", "Yes")
    if any(k in q_lower for k in ["visa sponsor", "require sponsor", "sponsorship"]):
        return data.get("requires_visa_sponsorship", "No")
    if any(k in q_lower for k in ["worked here", "worked at", "previous employee", "worked for"]):
        return data.get("worked_here_before", "No")
    if any(k in q_lower for k in ["family member", "relative", "personal relationship"]):
        return data.get("has_family_at_company", "No")
    if any(k in q_lower for k in ["outside business", "advisory", "consulting", "board role"]):
        return data.get("has_outside_business", "No")
    if any(k in q_lower for k in ["willing to work", "work from", "bangalore", "bengaluru", "onsite", "on-site"]):
        return data.get("willing_to_work_onsite", "Yes")
    if any(k in q_lower for k in ["relocate", "relocation"]):
        return data.get("willing_to_relocate", "Yes")
    if any(k in q_lower for k in ["current.*ctc", "current.*compensation", "current.*salary", "current annual"]):
        return data.get("current_ctc", "6000000")
    if any(k in q_lower for k in ["expected.*ctc", "expected.*compensation", "expected.*salary"]):
        return data.get("expected_ctc", "6500000")
    if any(k in q_lower for k in ["notice period", "notice"]):
        return data.get("notice_period", "30")
    if any(k in q_lower for k in ["year", "experience"]):
        return data.get("years_experience", "10")
    if "gender" in q_lower:
        return data.get("gender", "Male")
    if "veteran" in q_lower:
        return data.get("veteran_status", "I am not a protected veteran")
    if "disability" in q_lower:
        return data.get("disability_status", "I don't wish to answer")

    # Check memory for exact/partial match
    q_key = q_lower[:60].replace(" ", "_")
    if q_key in data:
        return data[q_key]

    # Ask user
    print(f"\n[QUESTION] {question}")
    if options:
        for i, opt in enumerate(options):
            print(f"  {i+1}. {opt}")
        raw = input("Answer (number or text): ").strip()
        try:
            answer = options[int(raw) - 1] if raw.isdigit() else raw
        except (IndexError, ValueError):
            answer = raw
    else:
        answer = input("Answer: ").strip()

    if answer:
        data[q_key] = answer
        save(data)
    return answer
