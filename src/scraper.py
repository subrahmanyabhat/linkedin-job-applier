"""Scrapes LinkedIn job search results."""
from playwright.sync_api import Page


def search_jobs(page: Page, keywords: str, location: str = "India",
                easy_apply_only: bool = True, max_pages: int = 5) -> list[dict]:
    """Returns list of {id, title, company, location, easy_apply, url}."""
    from urllib.parse import quote

    kw = quote(keywords)
    loc = quote(location)
    ea = "&f_AL=true" if easy_apply_only else ""
    url = f"https://www.linkedin.com/jobs/search/?keywords={kw}&location={loc}{ea}&sortBy=DD"

    page.goto(url)
    page.wait_for_timeout(2000)

    jobs = []
    seen = set()

    for p in range(max_pages):
        page.wait_for_timeout(1000)
        new = page.evaluate("""() => {
            const seen2 = new Set();
            return Array.from(document.querySelectorAll('[class*="job-card-container"]')).map(card => {
                const a = card.querySelector('a[href*="/jobs/view/"]');
                const id = a?.href?.match(/\\/jobs\\/view\\/(\\d+)/)?.[1];
                if (!id || seen2.has(id)) return null;
                seen2.add(id);
                return {
                    id,
                    title: card.querySelector('[class*="job-card-list__title"]')?.textContent?.trim() || '',
                    company: card.querySelector('[class*="subtitle"]')?.textContent?.trim() || '',
                    location: card.querySelector('[class*="metadata"]')?.textContent?.trim() || '',
                    url: a?.href || '',
                };
            }).filter(Boolean);
        }""")
        for job in new:
            if job["id"] not in seen:
                seen.add(job["id"])
                jobs.append(job)

        # Next page
        next_btn = page.locator('button[aria-label="View next page"]')
        if next_btn.count():
            next_btn.click()
            page.wait_for_timeout(1500)
        else:
            break

    return jobs


def get_job_details(page: Page, job_id: str) -> dict:
    """Visit job page and return {apply_url, ats_type, is_easy_apply}."""
    page.goto(f"https://www.linkedin.com/jobs/view/{job_id}/")
    page.wait_for_timeout(1500)

    result = page.evaluate("""() => {
        const applyLink = document.querySelector('a[href*="/apply/"]');
        const noLonger = document.body.innerText.includes('No longer accepting');
        const easyApplyBtn = document.querySelector('button.jobs-apply-button');
        return {
            apply_url: applyLink?.href || '',
            is_easy_apply: !!applyLink || !!easyApplyBtn,
            no_longer_accepting: noLonger,
            title: document.querySelector('h1')?.textContent?.trim() || '',
            company: document.querySelector('[class*="company-name"]')?.textContent?.trim() || '',
        };
    }""")

    # Detect ATS type from external redirect
    ats = "linkedin"
    url = result.get("apply_url", "")
    if "workday" in url or "myworkdayjobs" in url:
        ats = "workday"
    elif "greenhouse.io" in url:
        ats = "greenhouse"
    elif "lever.co" in url:
        ats = "lever"
    elif "ashbyhq.com" in url:
        ats = "ashby"
    elif url and "linkedin.com" not in url:
        ats = "external"

    result["ats"] = ats
    return result
