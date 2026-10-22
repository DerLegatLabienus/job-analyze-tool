from pydantic import BaseModel


class JobRef(BaseModel):
    """A job as seen in an alert email, before its description is fetched."""

    job_id: str
    url: str
    title: str
    company: str = ""
    location: str = ""
    source_msg_id: str = ""
