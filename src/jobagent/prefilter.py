"""Cheap, LLM-free filters. Mid-level at corporates is decided later (M2)."""
import re

from .config import Filters
from .models import JobRef


def prefilter(job: JobRef, f: Filters) -> tuple[str, str | None]:
    """Return (state, reason): 'filtered_out' with a reason, or 'discovered'."""
    if re.search(f.reject_title_regex, job.title, re.I):
        return "filtered_out", "junior_title"
    return "discovered", None


def needs_corporate_check(job: JobRef, f: Filters) -> bool:
    return bool(re.search(f.flag_title_regex, job.title, re.I))
