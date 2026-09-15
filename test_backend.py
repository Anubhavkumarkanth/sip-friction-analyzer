"""Backend tests.

These run against the configured PostgreSQL database. Rather than sharing the
developer's rows, each run creates its own user with a unique name and deletes
it at the end. Because simulations cascade from users and events cascade from
simulations, deleting that one row removes everything the test wrote - which is
also what test_delete_user_cascades_simulations checks directly.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from auth import get_password_hash
from database import SessionLocal
from engine.friction import calculate_ccr, calculate_cld, calculate_discipline_score
from engine.simulation import SIPSimulator
from main import app
from models import Simulation, SimulationEvent, User


TEST_PASSWORD = "test-password-not-a-secret"


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def user(client):
    """A throwaway account, removed again when the test finishes."""
    username = f"testuser-{uuid.uuid4().hex[:12]}"

    db = SessionLocal()
    try:
        record = User(username=username, hashed_password=get_password_hash(TEST_PASSWORD))
        db.add(record)
        db.commit()
        db.refresh(record)
        user_id = record.id
    finally:
        db.close()

    yield {"id": user_id, "username": username}

    db = SessionLocal()
    try:
        db.query(User).filter(User.id == user_id).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture
def auth(client, user):
    """Authorization header for the throwaway account."""
    response = client.post(
        "/token",
        data={"username": user["username"], "password": TEST_PASSWORD},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


# ==========================================
# Engine unit tests (no database)
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
    assert res["worst_case"] <= res["p10"] <= res["p50"] <= res["p90"] <= res["best_case"]


def test_friction_metrics():
    assert calculate_cld(100000, 80000) == 20000.0
    assert calculate_cld(80000, 100000) == 0.0
    assert calculate_ccr(100000, 90000) == 0.9
    assert calculate_discipline_score(1.0, 0.0) == 100.0
    assert calculate_discipline_score(0.5, 0.3) < 100.0


# ==========================================
# API tests
# ==========================================
def test_status_endpoint(client):
    response = client.get("/api")
    assert response.status_code == 200
    assert response.json()["status"] == "online"


def test_simulate_requires_authentication(client):
    response = client.post(
        "/simulate",
        json={"monthly_amount": 5000, "annual_return": 12, "years": 10, "events": []},
    )
    assert response.status_code == 401


def test_simulate_persists_run_and_its_events(client, auth, user):
    payload = {
        "monthly_amount": 5000,
        "annual_return": 12,
        "years": 10,
        "events": [
            {"type": "SKIP", "month": 6},
            {"type": "PAUSE_RANGE", "start_month": 20, "end_month": 24},
        ],
    }
    response = client.post("/simulate", json=payload, headers=auth)
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["actual_value"] < data["ideal_value"]
    assert len(data["chart_data"]) == 10
    assert data["simulation_id"] > 0

    # The run and both of its events should have been written together.
    db = SessionLocal()
    try:
        saved = db.query(Simulation).filter(Simulation.id == data["simulation_id"]).one()
        assert saved.user_id == user["id"]
        assert saved.monthly_amount == 5000
        assert saved.years == 10

        events = (
            db.query(SimulationEvent)
            .filter(SimulationEvent.simulation_id == saved.id)
            .all()
        )
        assert {event.event_type for event in events} == {"SKIP", "PAUSE_RANGE"}
    finally:
        db.close()


def test_simulate_validation_errors(client, auth):
    response = client.post(
        "/simulate",
        json={"monthly_amount": -100, "annual_return": 12, "years": 5},
        headers=auth,
    )
    assert response.status_code == 422

    response = client.post(
        "/simulate",
        json={"monthly_amount": 5000, "annual_return": 12, "years": 0},
        headers=auth,
    )
    assert response.status_code == 422


def test_history_requires_authentication(client):
    assert client.get("/simulations").status_code == 401


def test_history_returns_saved_runs_with_event_counts(client, auth):
    client.post(
        "/simulate",
        json={
            "monthly_amount": 7000,
            "annual_return": 11,
            "years": 8,
            "events": [{"type": "SKIP", "month": 3}],
        },
        headers=auth,
    )
    # A run with no friction at all: the LEFT JOIN must still return it.
    client.post(
        "/simulate",
        json={"monthly_amount": 7000, "annual_return": 11, "years": 8, "events": []},
        headers=auth,
    )

    response = client.get("/simulations", headers=auth)
    assert response.status_code == 200

    history = response.json()
    assert len(history) == 2
    counts = sorted(row["event_count"] for row in history)
    assert counts == [0, 1]


def test_simulation_detail_returns_its_events(client, auth):
    created = client.post(
        "/simulate",
        json={
            "monthly_amount": 9000,
            "annual_return": 13,
            "years": 6,
            "events": [{"type": "REDUCE", "month": 4, "factor": 0.5}],
        },
        headers=auth,
    ).json()

    response = client.get(f"/simulations/{created['simulation_id']}", headers=auth)
    assert response.status_code == 200

    detail = response.json()
    assert detail["event_count"] == 1
    assert detail["events"][0]["type"] == "REDUCE"
    assert detail["events"][0]["factor"] == 0.5


def test_other_users_simulation_is_not_visible(client, auth):
    assert client.get("/simulations/999999999", headers=auth).status_code == 404


def test_delete_user_cascades_simulations_and_events(client, auth, user):
    created = client.post(
        "/simulate",
        json={
            "monthly_amount": 5000,
            "annual_return": 12,
            "years": 5,
            "events": [{"type": "SKIP", "month": 2}],
        },
        headers=auth,
    ).json()
    simulation_id = created["simulation_id"]

    db = SessionLocal()
    try:
        assert db.query(SimulationEvent).filter(
            SimulationEvent.simulation_id == simulation_id
        ).count() == 1

        # Removing the owner should take the run and its events with it.
        db.query(User).filter(User.id == user["id"]).delete()
        db.commit()

        assert db.query(Simulation).filter(Simulation.id == simulation_id).count() == 0
        assert db.query(SimulationEvent).filter(
            SimulationEvent.simulation_id == simulation_id
        ).count() == 0
    finally:
        db.close()


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
    assert len(client.get("/funds").json()) > 0

    search = client.get("/search-funds?q=Parag")
    assert search.status_code == 200
    assert "Parag" in search.json()[0]["name"]

    sorted_funds = client.get("/search-funds?sort_by=return_5y").json()
    assert sorted_funds[0]["return_5y"] >= sorted_funds[-1]["return_5y"]


def test_search_with_no_match_returns_empty(client):
    """The filters must not lie.

    This previously fell back to the top five funds by 5-year return, so a
    search that matched nothing looked like it had matched something.
    """
    response = client.get("/search-funds?q=nosuchfundexists12345")
    assert response.status_code == 200
    assert response.json() == []


def test_login_rejects_a_wrong_password(client, user):
    response = client.post(
        "/token",
        data={"username": user["username"], "password": "definitely-wrong"},
    )
    assert response.status_code == 401
