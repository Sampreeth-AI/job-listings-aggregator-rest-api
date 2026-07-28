"""Starter data so a new public demo is useful immediately."""
from app import db
from app.models import Job

DEMO_JOBS = (
    {"title": "Python Backend Developer", "company": "RoleRadar Demo",
     "location": "Remote", "url": "https://example.com/jobs/python-backend",
     "source": "demo", "skills": "python,flask,mysql"},
    {"title": "Data Analyst", "company": "RoleRadar Demo",
     "location": "Bengaluru, India", "url": "https://example.com/jobs/data-analyst",
     "source": "demo", "skills": "python,sql,data"},
    {"title": "Frontend Engineer", "company": "RoleRadar Demo",
     "location": "Remote", "url": "https://example.com/jobs/frontend-engineer",
     "source": "demo", "skills": "javascript,typescript,react"},
)


def seed_demo_jobs() -> None:
    """Insert safe sample listings only when a new database is empty."""
    if Job.query.first():
        return
    db.session.add_all(Job(**job) for job in DEMO_JOBS)
    db.session.commit()
