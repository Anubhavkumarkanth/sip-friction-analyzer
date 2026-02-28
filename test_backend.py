from fastapi.testclient import TestClient
from main import app, Base, engine
from models import User

def test_login_and_auth():
    with TestClient(app) as client:
        # Attempt to access protected route without token
        response = client.get("/funds")
        assert response.status_code == 401

        # Login
        response = client.post("/token", data={"username": "testuser", "password": "password123"})
        assert response.status_code == 200
        token = response.json().get("access_token")
        assert token is not None
        return token

def test_simulate(token):
    with TestClient(app) as client:
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "monthly_amount": 5000,
            "annual_return": 12,
            "years": 10,
            "events": [
                {"type": "SKIP", "month": 6}
            ]
        }
        response = client.post("/simulate", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "ideal_value" in data
        assert "compounding_loss" in data

