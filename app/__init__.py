"""Application factory and extensions."""
import atexit
import os

from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
scheduler = BackgroundScheduler(daemon=True)


def create_app() -> Flask:
    load_dotenv()
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "development-only-secret"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///jobs.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        DEBUG=os.getenv("FLASK_ENV") == "development",
    )
    db.init_app(app)

    from app.api import api
    app.register_blueprint(api, url_prefix="/api/v1")

    @app.get("/")
    def home():
        return render_template("index.html")

    with app.app_context():
        from app.models import Job  # Ensure metadata is registered before create_all.
        db.create_all()

    _start_scheduler(app)
    return app


def _start_scheduler(app: Flask) -> None:
    """Schedule scraping once per process (avoid duplicate Flask reloader jobs)."""
    if scheduler.running:
        return
    if app.debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        return

    from app.services.scraper import scrape_all_sources

    interval = int(os.getenv("SCRAPE_INTERVAL_MINUTES", "60"))

    def scheduled_scrape():
        with app.app_context():
            scrape_all_sources()

    scheduler.add_job(scheduled_scrape, "interval", minutes=interval,
                      id="job-scraper", replace_existing=True)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown(wait=False))
