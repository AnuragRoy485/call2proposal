from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
BODY = {"proposal_markdown":"# Proposal\n\n## Commercials\nTo be confirmed\n\n## Next step\nReview and approve.","run_id":"abcdef12"}

def test_export_rejected_without_human_approval():
    response = client.post("/v1/export/docx", json={**BODY,"approved":False})
    assert response.status_code == 409

def test_approved_docx_export():
    response = client.post("/v1/export/docx", json={**BODY,"approved":True})
    assert response.status_code == 200
    assert response.content[:2] == b"PK"
    assert response.headers["content-type"].startswith("application/vnd.openxmlformats")
