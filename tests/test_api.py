import os
import unittest

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["FLASK_ENV"] = "testing"

from app import create_app, db


class JobApiTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            
    def test_delete_requires_api_key(self):
        response = self.client.delete("/api/v1/jobs/1")
        self.assertEqual(response.status_code, 401)

    def test_create_and_filter_jobs(self):
        response = self.client.post("/api/v1/jobs", json={
            "title": "Python Developer", "company": "Acme", "location": "Remote",
            "url": "https://example.com/jobs/1", "source": "manual", "skills": "python,flask"})
        self.assertEqual(response.status_code, 201)
        response = self.client.get("/api/v1/jobs?search=Python&location=remote")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["total"], 1)
        self.assertEqual(self.client.get("/api/v1/jobs?skills=flask").json["total"], 1)


if __name__ == "__main__":
    unittest.main()

