from pathlib import Path

from jobagent.alerts import extract_job_id, parse_alert_html
from jobagent.config import Filters
from jobagent.ingest import ingest
from jobagent.store import Store

HTML = (Path(__file__).parent / "fixtures/linkedin_alert.html").read_text()


def test_extract_job_id_variants():
    assert extract_job_id("https://www.linkedin.com/comm/jobs/view/3912345678/?t=1") == "3912345678"
    assert extract_job_id("https://www.linkedin.com/jobs/view/senior-dev-at-x-3999999999?x=1") == "3999999999"
    assert extract_job_id("https://www.linkedin.com/jobs/search/?currentJobId=4000000002") == "4000000002"
    assert extract_job_id("https://www.linkedin.com/jobs/search/?keywords=x") is None


def test_parse_dedupes_and_extracts_fields():
    jobs = parse_alert_html(HTML, "m1")
    assert [j.job_id for j in jobs] == ["3912345678", "3999999999", "4000000001"]
    first = jobs[0]
    assert first.title == "Senior Backend Engineer"
    assert first.company == "Acme Fintech"
    assert first.location == "Tel Aviv, Israel"
    assert first.url == "https://www.linkedin.com/jobs/view/3912345678/"


def test_ingest_filters_junior_and_is_idempotent():
    store = Store(":memory:")
    s1 = ingest([("m1", HTML)], store, Filters())
    assert (s1.messages, s1.jobs_seen, s1.new, s1.filtered) == (1, 3, 3, 1)
    assert store.counts() == {"discovered": 2, "filtered_out": 1}
    s2 = ingest([("m1", HTML)], store, Filters())  # same message again
    assert s2.messages == 0 and s2.new == 0
    s3 = ingest([("m2", HTML)], store, Filters())  # new message, known jobs
    assert s3.new == 0
    assert store.counts() == {"discovered": 2, "filtered_out": 1}


def test_view_cap_counter():
    store = Store(":memory:")
    store.record_view("1")
    store.record_view("2")
    assert store.views_today() == 2
