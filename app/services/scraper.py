"""Source adapters. Only scrape sources whose terms and robots policy permit it."""
from dataclasses import dataclass
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from app import db
from app.models import Job

HEADERS = {"User-Agent": "JobListingsAggregator/1.0 (contact: admin@example.com)"}


@dataclass(frozen=True)
class HtmlSource:
    name: str
    url: str
    card_selector: str
    title_selector: str
    company_selector: str
    link_selector: str
    location_selector: str | None = None


# Add only sources you have permission to fetch; selectors are intentionally explicit.
SOURCES: list[HtmlSource] = []


def scrape_all_sources() -> dict:
    created = updated = failed = 0
    for source in SOURCES:
        try:
            result = scrape_html_source(source)
            created += result["created"]
            updated += result["updated"]
        except (requests.RequestException, ValueError) as exc:
            failed += 1
            print(f"Scrape failed for {source.name}: {exc}")
    return {"created": created, "updated": updated, "failed_sources": failed}


def scrape_html_source(source: HtmlSource) -> dict:
    response = requests.get(source.url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    created = updated = 0
    for card in soup.select(source.card_selector):
        title = _text(card, source.title_selector)
        company = _text(card, source.company_selector)
        anchor = card.select_one(source.link_selector)
        if not (title and company and anchor and anchor.get("href")):
            continue
        url = urljoin(source.url, anchor["href"])
        location = _text(card, source.location_selector) if source.location_selector else None
        job = Job.query.filter_by(url=url).first()
        if job:
            job.title, job.company, job.location = title, company, location
            updated += 1
        else:
            db.session.add(Job(title=title, company=company, location=location,
                               url=url, source=source.name))
            created += 1
    db.session.commit()
    return {"created": created, "updated": updated}


def _text(node, selector: str | None) -> str | None:
    if not selector or not (element := node.select_one(selector)):
        return None
    return element.get_text(" ", strip=True) or None

