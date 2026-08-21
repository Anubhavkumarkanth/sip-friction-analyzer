import pytest
from fastapi.testclient import TestClient

from main import app
from engine.simulation import SIPSimulator
from engine.friction import calculate_ccr, calculate_cld, calculate_discipline_score


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


# ==========================================
# Unit Tests for Engine
# ==========================================
def test_engine_ideal_simulation():
    sim = SIPSimulator(monthly_amount=10000, annual_return=0.12, years=10)
    ideal, history = sim.calculate_ideal()
    assert ideal > 0
    assert len(history) == 10
    assert history[-1]["year"] == 10
    assert history[-1]["ideal_value"] == ideal


def test_engine_friction_events():
    sim = SIPSimulator(monthly_amount=10000, annual_return=0.12, years=5)
    events = [
        {"type": "SKIP", "month": 6},
        {"type": "REDUCE", "month": 12, "factor": 0.5},
        {"type": "PAUSE_RANGE", "start_month": 20, "end_month": 22},
        {"type": "STEP_UP", "yearly_growth": 0.10}
    ]
    actual, total_expected, total_actual, history = sim.calculate_actual(events)
    assert total_actual < total_expected
    assert actual > 0
    assert len(history) == 5


def test_engine_monte_carlo_distribution():
    sim = SIPSimulator(monthly_amount=5000, annual_return=0.12, years=5)
    res = sim.monte_carlo(events=[], simulations=200, volatility=0.15)
    assert "mean" in res
    assert "p10" in res
    assert "p50" in res
    assert "p90" in res
    assert res["worst_case"] <= res["p10"] <= res["p50"] <= res["p90"] <= res["best_case"]


def test_friction_metrics():
    assert calculate_cld(100000, 80000) == 20000.0
    assert calculate_cld(80000, 100000) == 0.0
    assert calculate_ccr(100000, 90000) == 0.9
    assert calculate_discipline_score(1.0, 0.0) == 100.0
    assert calculate_discipline_score(0.5, 0.3) < 100.0


# ==========================================
# Integration Tests for API Endpoints
# ==========================================
def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "service" in data


def test_simulate_endpoint(client):
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
    assert "actual_value" in data
    assert "compounding_loss" in data
    assert "discipline_score" in data
    assert data["actual_value"] < data["ideal_value"]
    assert len(data["chart_data"]) == 10


def test_simulate_validation_errors(client):
    # Invalid monthly amount
    response = client.post("/simulate", json={"monthly_amount": -100, "annual_return": 12, "years": 5})
    assert response.status_code == 422

    # Invalid years
    response = client.post("/simulate", json={"monthly_amount": 5000, "annual_return": 12, "years": 0})
    assert response.status_code == 422


def test_monte_carlo_endpoint(client):
    payload = {
        "monthly_amount": 5000,
        "annual_return": 12,
        "years": 5,
        "events": [],
        "simulations": 50,
        "volatility": 0.15
    }
    response = client.post("/monte-carlo", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["worst_case"] <= data["p50"] <= data["best_case"]


def test_funds_list_and_search(client):
    # Get all funds
    res = client.get("/funds")
    assert res.status_code == 200
    funds = res.json()
    assert len(funds) > 0

    # Search fund by query
    search_res = client.get("/search-funds?q=Parag")
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert len(search_data) >= 1
    assert "Parag" in search_data[0]["name"]

    # Search with sort
    sort_res = client.get("/search-funds?sort_by=return_5y")
    assert sort_res.status_code == 200
    sort_data = sort_res.json()
    assert sort_data[0]["return_5y"] >= sort_data[-1]["return_5y"]


def test_auth_login_flow(client):
    # Successful login with default admin credentials
    res = client.post("/token", data={"username": "admin", "password": "admin123"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Failed login
    bad_res = client.post("/token", data={"username": "admin", "password": "wrongpassword"})
    assert bad_res.status_code == 401
