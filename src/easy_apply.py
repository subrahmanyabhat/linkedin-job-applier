"""LinkedIn Easy Apply modal handler."""
import re
from pathlib import Path
from playwright.sync_api import Page
from . import memory, tracker


def _fill_step(page: Page, resume_path: str, mem: dict):
    """Fill all fields on current modal step."""
    modal = page.locator(".jobs-easy-apply-modal")

    # Checkboxes — check all unchecked
    for cb in modal.locator("input[type=checkbox]").all():
        if not cb.is_checked():
            cb.click()

    # Radio groups
    radio_groups: dict[str, list] = {}
    for radio in modal.locator("input[type=radio]").all():
        name = radio.get_attribute("name") or ""
        radio_groups.setdefault(name, []).append(radio)

    for name, group in radio_groups.items():
        if any(r.is_checked() for r in group):
            continue  # already answered
        # Find question text from fieldset legend
        first = group[0]
        try:
            legend = first.locator("xpath=ancestor::fieldset//legend").first.inner_text()
        except Exception:
            legend = ""
        answer = memory.answer_question(legend or name, options=None)
        # Find radio whose label matches answer
        matched = None
        for r in group:
            rid = r.get_attribute("id") or ""
            lbl = page.locator(f'label[for="{rid}"]')
            if lbl.count() and answer.lower() in (lbl.first.inner_text().lower()):
                matched = r
                break
        if matched is None:
            # default: last option (usually "No")
            matched = group[-1]
        rid = matched.get_attribute("id") or ""
        lbl = page.locator(f'label[for="{rid}"]')
        if lbl.count():
            lbl.first.click()
        else:
            matched.click()

    # Text inputs
    for inp in modal.locator("input[type=text]").all():
        try:
            if inp.input_value():
                continue
        except Exception:
            continue
        el_id = inp.get_attribute("id") or ""
        label_el = page.locator(f'label[for="{el_id}"]')
        label_text = label_el.first.inner_text().lower() if label_el.count() else ""

        if "location" in el_id or "location" in label_text:
            city = mem.get("city", "Bengaluru")
            inp.fill(city)
            page.wait_for_timeout(1200)
            opt = page.locator('li[role="option"], [class*="basic-typeahead__selectable"]').first
            if opt.count():
                opt.click()
        elif "first" in label_text:
            inp.fill(mem.get("first_name", "Subrahmanya"))
        elif "last" in label_text:
            inp.fill(mem.get("last_name", "Bhat"))
        elif "phone" in label_text or "mobile" in label_text:
            inp.fill(mem.get("phone", "9480420288"))
        elif "linkedin" in label_text or "linkedin" in el_id.lower():
            inp.fill(mem.get("linkedin_url", ""))
        elif "website" in label_text or "website" in el_id.lower():
            pass  # optional, skip
        elif "headline" in label_text:
            inp.fill(mem.get("headline", ""))
        elif any(k in label_text for k in ["ctc", "current.*salary", "current.*comp", "current annual"]):
            inp.fill(mem.get("current_ctc", "6000000"))
        elif any(k in label_text for k in ["expected", "desired"]):
            inp.fill(mem.get("expected_ctc", "6500000"))
        elif "notice" in label_text:
            inp.fill(mem.get("notice_period", "30"))
        elif any(k in label_text for k in ["year", "experience"]):
            inp.fill(mem.get("years_experience", "10"))
        else:
            # Unknown — ask user
            answer = memory.answer_question(label_text or el_id)
            if answer:
                inp.fill(answer)

    # Selects
    for sel in modal.locator("select").all():
        try:
            current = sel.input_value()
        except Exception:
            continue
        if current not in ("Select an option", ""):
            continue
        el_id = sel.get_attribute("id") or ""
        label_el = page.locator(f'label[for="{el_id}"]')
        label_text = label_el.first.inner_text().lower() if label_el.count() else ""
        options = sel.locator("option").all_inner_texts()
        real_opts = [o for o in options if o not in ("Select an option", "")]

        if "email" in label_text:
            target = mem.get("email", "")
            if target in real_opts:
                sel.select_option(target)
        elif "country" in label_text and "phone" in label_text:
            sel.select_option("India (+91)")
        elif any(k in label_text for k in ["willing", "bangalore", "bengaluru", "onsite", "authorized"]):
            if "Yes" in real_opts:
                sel.select_option("Yes")
        elif any(k in label_text for k in ["sponsor", "visa"]):
            if "No" in real_opts:
                sel.select_option("No")
        else:
            answer = memory.answer_question(label_text or el_id, options=real_opts)
            if answer in real_opts:
                sel.select_option(answer)
            elif real_opts:
                sel.select_option(real_opts[0])

    # Textareas (cover letter)
    for ta in modal.locator("textarea").all():
        try:
            if ta.input_value():
                continue
        except Exception:
            continue
        ta.fill(mem.get("cover_letter", "NA"))

    # Resume upload
    upload = modal.locator("input[type=file]")
    if upload.count() and resume_path and Path(resume_path).exists():
        try:
            upload.first.set_input_files(resume_path)
            page.wait_for_timeout(1000)
        except Exception:
            pass


def apply(page: Page, job_id: str, title: str, company: str,
          location: str, resume_path: str) -> str:
    """
    Run the full Easy Apply flow for the current job.
    Returns: 'submitted' | 'skipped' | 'error:<msg>'
    """
    mem = memory.load()

    job_url = f"https://www.linkedin.com/jobs/view/{job_id}/"
    page.goto(job_url)
    page.wait_for_timeout(1500)

    if tracker.already_applied(job_id):
        print(f"  [SKIP] Already applied: {company} - {title}")
        return "skipped"

    # Find apply link
    apply_link = page.locator("a[href*='/apply/']")
    if not apply_link.count():
        # Check for external ATS
        ext_btn = page.locator("button.jobs-apply-button, [class*='apply-button']")
        if ext_btn.count():
            href = ext_btn.first.get_attribute("href") or ""
            # External site
            ext_url = page.evaluate("() => document.querySelector('a[class*=apply]')?.href || ''")
            tracker.log_third_party(job_id, title, company, ext_url or "unknown", job_url)
            tracker.log_applied(job_id, title, company, location, job_url, "external", "saved_link")
            return "external"
        return "no-apply"

    apply_url = apply_link.first.get_attribute("href") or ""
    page.goto(apply_url)
    page.wait_for_timeout(1200)

    for step in range(15):
        page.wait_for_timeout(700)
        modal = page.locator(".jobs-easy-apply-modal")
        if not modal.count():
            tracker.log_applied(job_id, title, company, location, job_url, "easy_apply", "submitted")
            return "submitted"

        _fill_step(page, resume_path, mem)
        page.wait_for_timeout(400)

        # Click Next / Review / Submit
        submitted = False
        for btn_label in ["Submit application", "Review", "Next"]:
            btn = modal.locator(f"button:visible >> text='{btn_label}'")
            if btn.count():
                btn.first.click()
                if btn_label == "Submit application":
                    submitted = True
                break

        if submitted:
            page.wait_for_timeout(1500)
            tracker.log_applied(job_id, title, company, location, job_url, "easy_apply", "submitted")
            return "submitted"

    return "max-steps"
