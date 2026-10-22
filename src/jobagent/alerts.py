"""Parse LinkedIn job-alert emails into JobRefs. Pure functions, no network."""
import re

from bs4 import BeautifulSoup

from .models import JobRef

_JOB_ID = re.compile(r"/jobs/view/(?:[^/?]*?-)?(\d{6,})")
_JOB_ID_PARAM = re.compile(r"[?&]currentJobId=(\d{6,})")


def extract_job_id(url: str) -> str | None:
    m = _JOB_ID.search(url) or _JOB_ID_PARAM.search(url)
    return m.group(1) if m else None


def canonical_url(job_id: str) -> str:
    return f"https://www.linkedin.com/jobs/view/{job_id}/"


def parse_alert_html(html: str, source_msg_id: str = "") -> list[JobRef]:
    """Each job card is an <a> to /jobs/view/<id>; company/location follow as text.

    LinkedIn's markup changes; we rely only on link structure and the first
    non-empty text lines after the title, and keep fixtures to detect drift.
    """
    soup = BeautifulSoup(html, "html.parser")
    seen: dict[str, JobRef] = {}
    for a in soup.find_all("a", href=True):
        job_id = extract_job_id(a["href"])
        title = a.get_text(" ", strip=True)
        if not job_id or not title or job_id in seen:
            continue
        company = location = ""
        card = a.find_parent(["td", "div", "li"])
        if card:
            lines = [
                s.strip()
                for s in card.get_text("\n").split("\n")
                if s.strip() and s.strip() != title
            ]
            company = lines[0] if lines else ""
            if len(lines) > 1:
                location = lines[1]
        seen[job_id] = JobRef(
            job_id=job_id,
            url=canonical_url(job_id),
            title=title,
            company=company,
            location=location,
            source_msg_id=source_msg_id,
        )
    return list(seen.values())
