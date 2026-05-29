"""Workday ATS application handler."""
import time
from playwright.sync_api import Page
from . import memory, tracker


def _is_workday(url: str) -> bool:
    return "myworkdayjobs.com" in url or "wd" in url and "workday" in url


def apply(page: Page, job_id: str, title: str, company: str,
          location: str, workday_url: str, resume_path: str) -> str:
    mem = memory.load()

    if tracker.already_applied(job_id):
        print(f"  [SKIP] Already applied: {company} - {title}")
        return "skipped"

    print(f"  [WORKDAY] Applying: {company} - {title}")
    page.goto(workday_url)
    page.wait_for_timeout(2000)

    # Try to find Apply button
    apply_btn = page.locator("a:has-text('Apply'), button:has-text('Apply'), a:has-text('Apply Now')")
    if apply_btn.count():
        apply_btn.first.click()
        page.wait_for_timeout(2000)

    # Handle "Create Account" or "Sign In" for Workday
    create_acct = page.locator("button:has-text('Create Account'), a:has-text('Create Account')")
    if create_acct.count():
        create_acct.first.click()
        page.wait_for_timeout(1500)
        # Fill account creation form
        email = mem.get("email", "")
        for field in ["email", "Email"]:
            el = page.locator(f"input[autocomplete='email'], input[type='email'], input[placeholder*='mail']")
            if el.count():
                el.first.fill(email)
                break
        # Password fields
        pwd_fields = page.locator("input[type='password']").all()
        for pf in pwd_fields:
            pf.fill("Bhat@365days")
        # Checkbox consent
        for cb in page.locator("input[type='checkbox']").all():
            if not cb.is_checked():
                cb.click()
        submit = page.locator("button[type='submit']:visible, button:has-text('Create'):visible")
        if submit.count():
            submit.first.click()
            page.wait_for_timeout(2000)

    # Multi-step Workday form
    for step in range(20):
        page.wait_for_timeout(1000)

        # Upload resume
        file_input = page.locator("input[type='file']")
        if file_input.count() and resume_path:
            from pathlib import Path
            if Path(resume_path).exists():
                try:
                    file_input.first.set_input_files(resume_path)
                    page.wait_for_timeout(1500)
                except Exception:
                    pass

        # Fill text fields
        for inp in page.locator("input[type='text']:visible, input[type='email']:visible").all():
            try:
                if inp.input_value():
                    continue
            except Exception:
                continue
            placeholder = (inp.get_attribute("placeholder") or "").lower()
            aria_label = (inp.get_attribute("aria-label") or "").lower()
            label_text = placeholder or aria_label

            if any(k in label_text for k in ["first", "given"]):
                inp.fill(mem.get("first_name", "Subrahmanya"))
            elif any(k in label_text for k in ["last", "family", "surname"]):
                inp.fill(mem.get("last_name", "Bhat"))
            elif "email" in label_text:
                inp.fill(mem.get("email", ""))
            elif "phone" in label_text:
                inp.fill(mem.get("phone", "9480420288"))
            elif "city" in label_text or "location" in label_text:
                inp.fill(mem.get("city", "Bengaluru"))
            elif any(k in label_text for k in ["linkedin", "profile url"]):
                inp.fill(mem.get("linkedin_url", ""))

        # Radio buttons
        for radio in page.locator("input[type='radio']:visible").all():
            name = radio.get_attribute("name") or ""
            # Skip if group already answered
            group = page.locator(f"input[type='radio'][name='{name}']")
            if any(r.is_checked() for r in group.all()):
                continue
            radio.click()
            break

        # Check for Next / Continue / Submit
        for btn_text in ["Submit", "Next", "Continue", "Save and Continue"]:
            btn = page.locator(f"button:visible:has-text('{btn_text}'), input[type='submit'][value*='{btn_text}']")
            if btn.count():
                btn.first.click()
                page.wait_for_timeout(1500)
                if btn_text == "Submit":
                    tracker.log_applied(job_id, title, company, location,
                                        workday_url, "workday", "submitted")
                    return "submitted"
                break
        else:
            # No button found — might be done or stuck
            if "thank" in page.title().lower() or "submitted" in page.url.lower():
                tracker.log_applied(job_id, title, company, location,
                                    workday_url, "workday", "submitted")
                return "submitted"
            break

    tracker.log_third_party(job_id, title, company, workday_url,
                            f"https://www.linkedin.com/jobs/view/{job_id}/")
    tracker.log_applied(job_id, title, company, location, workday_url, "workday", "incomplete")
    return "incomplete"
