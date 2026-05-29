#!/usr/bin/env python3
"""
LinkedIn Job Applier CLI
Usage:
    python main.py apply --keywords "Engineering Manager" --location "Bengaluru, India"
    python main.py apply --job-ids 1234567890,9876543210
    python main.py status
"""
import os
import sys
from pathlib import Path

import click
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))
from src import memory, tracker, browser, easy_apply, scraper


def _get_credentials(email: str | None, password: str | None) -> tuple[str, str]:
    email = email or os.getenv("LINKEDIN_EMAIL") or memory.get(
        "email", "LinkedIn email")
    password = password or os.getenv("LINKEDIN_PASSWORD") or memory.get(
        "linkedin_password", "LinkedIn password")
    if email:
        memory.set_value("email", email)
    return email, password


def _get_resume(resume_path: str | None) -> str:
    path = (resume_path or os.getenv("RESUME_PATH") or
            memory.get("resume_path", "Path to resume PDF"))
    if path and Path(path).exists():
        memory.set_value("resume_path", path)
        return path
    click.echo(f"[ERROR] Resume not found: {path}", err=True)
    sys.exit(1)


@click.group()
def cli():
    pass


@cli.command()
@click.option("--keywords", "-k", default="Engineering Manager", show_default=True,
              help="Job search keywords")
@click.option("--location", "-l", default="Bengaluru, Karnataka, India", show_default=True)
@click.option("--job-ids", "-j", default="", help="Comma-separated specific job IDs")
@click.option("--max-pages", "-p", default=5, show_default=True)
@click.option("--apply-type", "-t", default="easy_apply",
              type=click.Choice(["easy_apply", "workday", "both"]), show_default=True)
@click.option("--email", "-e", default=None, envvar="LINKEDIN_EMAIL")
@click.option("--password", "-w", default=None, envvar="LINKEDIN_PASSWORD")
@click.option("--resume", "-r", default=None, envvar="RESUME_PATH")
@click.option("--headless", is_flag=True, default=False)
@click.option("--limit", default=50, show_default=True, help="Max jobs to apply")
def apply(keywords, location, job_ids, max_pages, apply_type, email, password, resume, headless, limit):
    """Search and apply to LinkedIn jobs."""
    email, password = _get_credentials(email, password)
    resume_path = _get_resume(resume)

    page = browser.get_page(headless=headless)
    if not browser.login(page, email, password):
        sys.exit(1)

    # Get job list
    if job_ids:
        jobs = [{"id": jid.strip(), "title": "", "company": "", "location": ""}
                for jid in job_ids.split(",")]
    else:
        click.echo(f"[SEARCH] {keywords} | {location}")
        easy_only = apply_type in ("easy_apply",)
        jobs = scraper.search_jobs(page, keywords, location,
                                   easy_apply_only=easy_only, max_pages=max_pages)
        click.echo(f"[FOUND] {len(jobs)} jobs")

    results = {"submitted": 0, "skipped": 0, "external": 0, "error": 0}
    applied = 0

    for job in jobs[:limit]:
        if applied >= limit:
            break

        job_id = job["id"]
        if tracker.already_applied(job_id):
            click.echo(f"  [SKIP] {job.get('company','?')} - {job.get('title','?')} (already applied)")
            results["skipped"] += 1
            continue

        # Get full job details if title/company missing
        if not job.get("title"):
            details = scraper.get_job_details(page, job_id)
            if details.get("no_longer_accepting"):
                click.echo(f"  [CLOSED] {job_id}")
                continue
            job.update(details)

        title = job.get("title", "")
        company = job.get("company", "")
        loc = job.get("location", "")

        # Skip director roles
        if any(w in title.lower() for w in ["director", "vp ", "vice president", "cto", "head of"]):
            click.echo(f"  [SKIP] Senior role: {title}")
            continue

        click.echo(f"\n[APPLY] {company} | {title} | {loc}")

        ats = job.get("ats", "linkedin")

        if ats == "workday" and apply_type in ("workday", "both"):
            result = easy_apply.apply(page, job_id, title, company, loc, resume_path)
        elif ats in ("linkedin", "greenhouse", "lever", "ashby", "external") or apply_type in ("easy_apply", "both"):
            result = easy_apply.apply(page, job_id, title, company, loc, resume_path)
        else:
            result = "skipped"

        click.echo(f"  [{result.upper()}]")
        results[result] = results.get(result, 0) + 1
        if result == "submitted":
            applied += 1

    click.echo(f"\n{'='*40}")
    click.echo(f"Done: {results['submitted']} submitted | {results.get('skipped',0)} skipped | "
               f"{results.get('external',0)} external saved")
    browser.close()


@cli.command()
def status():
    """Show applied jobs summary."""
    jobs = tracker.load_applied()
    if not jobs:
        click.echo("No applications yet.")
        return
    click.echo(f"\n{'='*60}")
    click.echo(f"{'Date':<18} {'Company':<20} {'Title':<30} {'Status'}")
    click.echo(f"{'='*60}")
    for j in jobs:
        click.echo(f"{j['date']:<18} {j['company'][:19]:<20} {j['title'][:29]:<30} {j['status']}")
    click.echo(f"\nTotal: {len(jobs)} applications")


@cli.command()
@click.argument("key")
@click.argument("value")
def remember(key, value):
    """Save a value to memory. E.g.: python main.py remember notice_period 60"""
    memory.set_value(key, value)
    click.echo(f"Saved: {key} = {value}")


if __name__ == "__main__":
    cli()
