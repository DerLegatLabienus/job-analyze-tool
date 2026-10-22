from dataclasses import dataclass
from typing import Iterable

from .alerts import parse_alert_html
from .config import Filters
from .prefilter import prefilter
from .store import Store


@dataclass
class IngestStats:
    messages: int = 0
    jobs_seen: int = 0
    new: int = 0
    filtered: int = 0


def ingest(messages: Iterable[tuple[str, str]], store: Store, filters: Filters) -> IngestStats:
    """Idempotent: already-processed messages and known job IDs are skipped."""
    stats = IngestStats()
    for msg_id, html in messages:
        if store.message_seen(msg_id):
            continue
        stats.messages += 1
        for job in parse_alert_html(html, msg_id):
            stats.jobs_seen += 1
            state, reason = prefilter(job, filters)
            if store.add_job(job, state, reason):
                stats.new += 1
                stats.filtered += state == "filtered_out"
        store.mark_message(msg_id)
    return stats
