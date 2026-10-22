from pathlib import Path

import typer

from .config import load_search
from .ingest import ingest
from .store import Store

app = typer.Typer(help="LinkedIn job agent (POC, milestone 1)")
KILL_SWITCH = Path("data/STOP")


def _guard() -> None:
    if KILL_SWITCH.exists():
        typer.echo("Kill-switch data/STOP present; refusing to run.")
        raise typer.Exit(1)


@app.command("ingest-alerts")
def ingest_alerts() -> None:
    """Read LinkedIn job-alert emails from Gmail and store new jobs."""
    _guard()
    from .gmail_source import fetch_alerts

    cfg = load_search()
    stats = ingest(fetch_alerts(cfg.gmail.query, cfg.gmail.max_messages), Store(), cfg.filters)
    typer.echo(stats)


@app.command("ingest-file")
def ingest_file(path: Path) -> None:
    """Ingest a saved alert email (.html), e.g. for offline testing."""
    cfg = load_search()
    stats = ingest([(path.name, path.read_text())], Store(), cfg.filters)
    typer.echo(stats)


@app.command("login")
def login_cmd() -> None:
    """One-time manual LinkedIn login in a headed browser."""
    from .fetcher import login

    login()


@app.command("fetch")
def fetch_cmd() -> None:
    """Fetch descriptions for discovered jobs (capped, jittered, stops on challenge)."""
    _guard()
    from .fetcher import fetch_descriptions

    cfg = load_search()
    typer.echo(f"fetched {fetch_descriptions(Store(), cfg.limits)} descriptions")


@app.command("status")
def status() -> None:
    """Show job counts by state and today's view count."""
    s = Store()
    typer.echo({"states": s.counts(), "views_today": s.views_today()})
