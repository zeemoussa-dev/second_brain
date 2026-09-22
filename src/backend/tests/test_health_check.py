from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check_returns_ok_status() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert isinstance(body["version"], str) and body["version"]


# BUG-068: an orphaned backend kept answering /health for a week while serving
# code from before a pull. The commit it loaded makes that visible from outside.
def test_health_reports_the_commit_the_running_code_was_loaded_from() -> None:
    import subprocess
    from pathlib import Path

    checkout = Path(__file__).resolve().parents[3]
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=checkout, capture_output=True, text=True).stdout.strip()

    body = client.get("/health").json()

    assert body["commit"] == head
