from fastapi.testclient import TestClient

from main import app


def test_root_endpoint():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "online"


def test_simulate():
    with TestClient(app) as client:
        payload = {
            "monthly_amount": 5000,
            "annual_return": 12,
            "years": 10,
            "events": [
                {"type": "SKIP", "month": 6}
            ]
        }
        response = client.post("/simulate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "ideal_value" in data
        assert "compounding_loss" in data
        assert data["actual_value"] < data["ideal_value"]


def test_validation_errors():
    with TestClient(app) as client:
        payload = {
            "monthly_amount": -5000,
            "annual_return": 12,
            "years": 10
        }
        response = client.post("/simulate", json=payload)
        assert response.status_code == 422


def test_monte_carlo():
    with TestClient(app) as client:
        payload = {
            "monthly_amount": 5000,
            "annual_return": 12,
            "years": 10,
            "events": [],
            "simulations": 10,
            "volatility": 0.2
        }
        response = client.post("/monte-carlo", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "mean" in data
