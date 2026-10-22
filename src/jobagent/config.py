from pathlib import Path

import yaml
from pydantic import BaseModel, Field

CONFIG_DIR = Path("config")


class GmailCfg(BaseModel):
    query: str = "from:jobalerts-noreply@linkedin.com newer_than:2d"
    max_messages: int = 50


class Limits(BaseModel):
    max_job_views_per_day: int = 100
    min_delay_s: float = 4
    max_delay_s: float = 12


class Filters(BaseModel):
    reject_title_regex: str = r"\b(junior|intern|student|graduate)\b"
    flag_title_regex: str = r"\b(mid|mid-level|ii)\b"


class SearchConfig(BaseModel):
    gmail: GmailCfg = Field(default_factory=GmailCfg)
    limits: Limits = Field(default_factory=Limits)
    filters: Filters = Field(default_factory=Filters)


def load_search(path: Path | None = None) -> SearchConfig:
    path = path or CONFIG_DIR / "search.yaml"
    if not path.exists():
        return SearchConfig()
    return SearchConfig.model_validate(yaml.safe_load(path.read_text()) or {})
