from flask import Blueprint, jsonify, request
from sqlalchemy import or_

from app import db
from app.models import Job
from app.services.scraper import scrape_all_sources

api = Blueprint("api", __name__)


@api.get("/health")
def health():
    return jsonify({"status": "ok"})


@api.get("/jobs")
def list_jobs():
    page = max(request.args.get("page", 1, type=int), 1)
    per_page = min(max(request.args.get("per_page", 20, type=int), 1), 100)
    query = Job.query

    search = request.args.get("search", "").strip()
    if search:
        term = f"%{search}%"
        query = query.filter(or_(Job.title.ilike(term), Job.company.ilike(term),
                                 Job.description.ilike(term)))
    for field in ("location", "source"):
        if value := request.args.get(field):
            query = query.filter(getattr(Job, field).ilike(f"%{value}%"))

    results = query.order_by(Job.posted_at.desc(), Job.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    return jsonify({"items": [job.to_dict() for job in results.items],
                    "page": page, "per_page": per_page, "total": results.total,
                    "pages": results.pages})


@api.get("/jobs/<int:job_id>")
def get_job(job_id):
    return jsonify(Job.query.get_or_404(job_id).to_dict())


@api.post("/jobs")
def create_job():
    data = request.get_json(silent=True) or {}
    required = ("title", "company", "url", "source")
    missing = [field for field in required if not data.get(field)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    if Job.query.filter_by(url=data["url"]).first():
        return jsonify({"error": "A job with this URL already exists"}), 409
    job = Job(**{key: data.get(key) for key in
                 ("title", "company", "location", "url", "source", "description")})
    db.session.add(job)
    db.session.commit()
    return jsonify(job.to_dict()), 201


@api.delete("/jobs/<int:job_id>")
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    return "", 204


@api.post("/scrape")
def scrape():
    """Run an on-demand aggregation. In production, protect this endpoint."""
    result = scrape_all_sources()
    return jsonify(result)

