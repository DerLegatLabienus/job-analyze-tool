"""Fetch full job descriptions via a logged-in browser session (needs `browser` extra).

Runs only for jobs that passed the pre-filter, under the daily view cap, with
jittered delays. Stops immediately on any login/challenge page.
"""
import random
import time
from pathlib import Path

from .config import Limits
from .store import Store

CHALLENGE_MARKERS = ("checkpoint/challenge", "authwall", "/login", "captcha")


class ChallengeDetected(RuntimeError):
    pass


def login(profile_dir: Path = Path("data/browser")) -> None:
    """Open a headed browser so you can log in manually (incl. 2FA). Session persists."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(str(profile_dir), headless=False)
        page = ctx.new_page()
        page.goto("https://www.linkedin.com/login")
        input("Log in in the browser window, then press Enter here... ")
        ctx.close()


def fetch_descriptions(store: Store, limits: Limits, profile_dir: Path = Path("data/browser")) -> int:
    from playwright.sync_api import sync_playwright

    fetched = 0
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(str(profile_dir), headless=False)
        page = ctx.new_page()
        for job in store.jobs_in_state("discovered"):
            if store.views_today() >= limits.max_job_views_per_day:
                break
            page.goto(job["url"], wait_until="domcontentloaded")
            if any(m in page.url.lower() for m in CHALLENGE_MARKERS):
                ctx.close()
                raise ChallengeDetected(page.url)
            store.record_view(job["job_id"])
            el = page.query_selector(".jobs-description__content, .show-more-less-html__markup")
            if el:
                store.set_description(job["job_id"], el.inner_text())
                fetched += 1
            time.sleep(random.uniform(limits.min_delay_s, limits.max_delay_s))
        ctx.close()
    return fetched
