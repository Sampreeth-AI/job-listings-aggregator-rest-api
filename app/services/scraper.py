"""Permitted source adapters used by the daily job import."""
from dataclasses import dataclass
from typing import Protocol
import warnings

import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

from app import db
from app.models import Job

HEADERS = {"User-Agent": "JobListingsAggregator/1.0 (contact: admin@example.com)"}


SKILL_KEYWORDS = ("python", "flask", "django", "fastapi", "java", "javascript",
                  "typescript", "react", "node", "sql", "mysql", "aws", "docker",
                  "devops", "data", "machine learning", "product", "design")


@dataclass(frozen=True)
class JobPayload:
    title: str
    company: str
    location: str
    url: str
    source: str
    description: str = ""
    skills: str = ""


class SourceAdapter(Protocol):
    name: str

    def fetch_jobs(self) -> list[JobPayload]: ...


@dataclass(frozen=True)
class RssSource:
    """We Work Remotely publishes and permits use of these attributed RSS feeds."""
    name: str
    url: str

    def fetch_jobs(self) -> list[JobPayload]:
        response = requests.get(self.url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        # The built-in parser keeps setup simple; RSS item tags are supported.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", XMLParsedAsHTMLWarning)
            feed = BeautifulSoup(response.content, "html.parser")
        jobs: list[JobPayload] = []
        for item in feed.find_all("item"):
            raw_title = item.title.get_text(" ", strip=True) if item.title else ""
            # WWR puts the canonical job URL in guid; its link tag is empty.
            link = item.guid.get_text(strip=True) if item.guid else ""
            description = item.description.get_text(" ", strip=True) if item.description else ""
            title, company = _split_rss_title(raw_title)
            if title and company and link:
                location = item.region.get_text(" ", strip=True) if item.region else "Remote"
                jobs.append(JobPayload(title, company, location, link, self.name,
                                       description, _extract_skills(f"{title} {description}")))
        return jobs


@dataclass(frozen=True)
class RemoteOkSource:
    """Remote OK exposes a public jobs feed; source attribution is retained."""
    name: str = "Remote OK"
    url: str = "https://remoteok.com/api"

    def fetch_jobs(self) -> list[JobPayload]:
        response = requests.get(self.url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        records = response.json()
        jobs: list[JobPayload] = []
        for record in records if isinstance(records, list) else []:
            if not isinstance(record, dict) or not record.get("position") or not record.get("company"):
                continue
            url = record.get("url") or f"https://remoteok.com/remote-jobs/{record.get('slug', '')}"
            tags = record.get("tags") or []
            skills = ",".join(str(tag).lower() for tag in tags) or _extract_skills(
                f"{record['position']} {record.get('description', '')}")
            jobs.append(JobPayload(record["position"], record["company"],
                                   record.get("location") or "Remote", url, self.name,
                                   record.get("description") or "", skills))
        return jobs


SOURCES: tuple[SourceAdapter, ...] = (
    RssSource("We Work Remotely · Programming", "https://weworkremotely.com/categories/remote-programming-jobs.rss"),
    RssSource("We Work Remotely · Design", "https://weworkremotely.com/categories/remote-design-jobs.rss"),
    RemoteOkSource(),
)


def scrape_all_sources() -> dict:
    created = updated = failed = 0
    for source in SOURCES:
        try:
            result = import_source(source)
            created += result["created"]
            updated += result["updated"]
        except (requests.RequestException, ValueError) as exc:
            db.session.rollback()
            failed += 1
            print(f"Scrape failed for {source.name}: {exc}")
    return {"created": created, "updated": updated, "failed_sources": failed}


def import_source(source: SourceAdapter) -> dict:
    created = updated = 0
    for payload in source.fetch_jobs():
        job = Job.query.filter_by(url=payload.url).first()
        if job:
            job.title, job.company, job.location = payload.title, payload.company, payload.location
            job.description, job.skills, job.source = payload.description, payload.skills, payload.source
            updated += 1
        else:
            db.session.add(Job(title=payload.title, company=payload.company,
                               location=payload.location, url=payload.url,
                               source=payload.source, description=payload.description,
                               skills=payload.skills))
            created += 1
    db.session.commit()
    return {"created": created, "updated": updated}


def _split_rss_title(raw_title: str) -> tuple[str, str]:
    """WWR RSS titles are generally formatted as 'Company: Role'."""
    if ":" in raw_title:
        company, title = raw_title.split(":", 1)
        return title.strip(), company.strip()
    if " at " in raw_title.lower():
        title, company = raw_title.rsplit(" at ", 1)
        return title.strip(), company.strip()
    return raw_title.strip(), "We Work Remotely"


def _extract_skills(text: str) -> str:
    normalized = text.lower()
    return ",".join(keyword for keyword in SKILL_KEYWORDS if keyword in normalized)
