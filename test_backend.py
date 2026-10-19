"""Backend tests.

These run against a dedicated PostgreSQL database: set TEST_DATABASE_URL to one
whose name ends in _test (see conftest.py, which refuses anything else). Rather
than sharing existing rows, each test creates its own users with unique names
and deletes them at the end. Because simulations cascade from users and events
cascade from simulations, deleting that one row removes everything the test
wrote - which is also what test_delete_user_cascades_simulations checks
directly.

The engine and metric tests that need no database are in test_engine.py.
"""

import datetime
import uuid

import jwt
import pytest
from fastapi.testclient import TestClient

from auth import get_password_hash
from config import settings
from database import SessionLocal
from main import app
from models import Simulation, SimulationEvent, User


TEST_PASSWORD = "test-password-not-a-secret"


@pytest.fixture
def client(test_database):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def make_user(client):
    """Factory for throwaway accounts, all removed again when the test finishes."""
    created = []

    def _make():
        username = f"testuser-{uuid.uuid4().hex[:12]}"
        db = SessionLocal()
        try:
            record = User(username=username, hashed_password=get_password_hash(TEST_PASSWORD))
            db.add(record)
            db.commit()
            db.refresh(record)
            created.append(record.id)
            return {"id": record.id, "username": username}
        finally:
            db.close()

    yield _make

    db = SessionLocal()
    try:
        db.query(User).filter(User.id.in_(created)).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


def bearer(client, account):
    response = client.post(
        "/token",
        data={"username": account["username"], "password": TEST_PASSWORD},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def user(make_user):
    """A throwaway account."""
    return make_user()


@pytest.fixture
def auth(client, user):
    """Authorization header for the throwaway account."""
    return bearer(client, user)


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


# ==========================================
# Request validation
# ==========================================
PLAN = {"monthly_amount": 5000, "annual_return": 12, "years": 5}


def simulate(client, auth, events):
    return client.post("/simulate", json={**PLAN, "events": events}, headers=auth)


@pytest.mark.parametrize(
    "event, complaint",
    [
        ({"type": "SKIP"}, "SKIP requires month"),
        ({"type": "REDUCE", "month": 3}, "REDUCE requires factor"),
        ({"type": "INCREASE", "month": 3}, "INCREASE requires factor"),
        ({"type": "PAUSE_RANGE", "start_month": 4}, "PAUSE_RANGE requires end_month"),
        ({"type": "STEP_UP"}, "STEP_UP requires yearly_growth"),
        ({"type": "PAUSE_RANGE", "start_month": 10, "end_month": 5}, "must not be before start_month"),
    ],
)
def test_an_event_missing_what_its_type_needs_is_a_422_not_a_500(client, auth, event, complaint):
    response = simulate(client, auth, [event])
    assert response.status_code == 422, response.text
    assert complaint in response.text


def test_an_event_must_start_inside_the_plan(client, auth):
    assert simulate(client, auth, [{"type": "SKIP", "month": 60}]).status_code == 200
    assert simulate(client, auth, [{"type": "SKIP", "month": 61}]).status_code == 422
    assert simulate(client, auth, [{"type": "PAUSE_RANGE", "start_month": 61, "end_month": 70}]).status_code == 422


def test_a_pause_may_run_past_the_end_of_the_plan(client, auth):
    response = simulate(client, auth, [{"type": "PAUSE_RANGE", "start_month": 50, "end_month": 999}])
    assert response.status_code == 200, response.text


def test_only_the_fields_an_event_uses_are_stored(client, auth):
    """The UI sends every field on every event; the stored row keeps the relevant ones."""
    created = simulate(
        client, auth,
        [{"type": "SKIP", "month": 3, "factor": 0.5, "yearly_growth": 0.1, "start_month": 12, "end_month": 24}],
    ).json()

    event = client.get(f"/simulations/{created['simulation_id']}", headers=auth).json()["events"][0]
    assert event == {
        "type": "SKIP", "month": 3, "factor": None,
        "yearly_growth": None, "start_month": None, "end_month": None,
    }


def test_history_is_newest_first_and_limit_is_bounded(client, auth):
    first = client.post("/simulate", json={**PLAN, "monthly_amount": 1000, "events": []}, headers=auth).json()
    second = client.post("/simulate", json={**PLAN, "monthly_amount": 2000, "events": []}, headers=auth).json()

    newest_only = client.get("/simulations?limit=1", headers=auth).json()
    assert [row["id"] for row in newest_only] == [second["simulation_id"]]
    assert [row["id"] for row in client.get("/simulations", headers=auth).json()] == [
        second["simulation_id"], first["simulation_id"],
    ]
    assert client.get("/simulations?limit=0", headers=auth).status_code == 422
    assert client.get("/simulations?limit=101", headers=auth).status_code == 422


def test_fund_paging_is_bounded(client):
    assert client.get("/funds?skip=-1").status_code == 422
    assert client.get("/funds?limit=0").status_code == 422
    assert client.get("/funds?limit=501").status_code == 422
    assert len(client.get("/funds?limit=2").json()) == 2


# ==========================================
# Who can see what
# ==========================================
def test_a_user_cannot_read_or_list_another_users_simulation(client, make_user):
    owner, intruder = make_user(), make_user()
    owner_auth, intruder_auth = bearer(client, owner), bearer(client, intruder)

    created = simulate(client, owner_auth, [{"type": "SKIP", "month": 2}]).json()
    run_id = created["simulation_id"]

    assert client.get(f"/simulations/{run_id}", headers=owner_auth).status_code == 200
    # 404, not 403: the response must not confirm that the id exists.
    assert client.get(f"/simulations/{run_id}", headers=intruder_auth).status_code == 404
    assert run_id in [row["id"] for row in client.get("/simulations", headers=owner_auth).json()]
    assert client.get("/simulations", headers=intruder_auth).json() == []


def test_login_fails_the_same_way_for_an_unknown_user_and_a_wrong_password(client, user):
    wrong_password = client.post("/token", data={"username": user["username"], "password": "nope"})
    unknown_user = client.post("/token", data={"username": "no-such-user-" + uuid.uuid4().hex, "password": "nope"})
    assert wrong_password.status_code == unknown_user.status_code == 401
    assert wrong_password.json() == unknown_user.json()


def make_token(subject, key=None, expires_in_minutes=5):
    claims = {"exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=expires_in_minutes)}
    if subject is not None:
        claims["sub"] = subject
    return jwt.encode(claims, key or settings.SECRET_KEY, algorithm="HS256")


def test_bad_tokens_are_rejected(client, user):
    name = user["username"]
    bad_tokens = {
        "garbage": "abc.def.ghi",
        "expired": make_token(name, expires_in_minutes=-5),
        "signed with another key": make_token(name, key="some-other-key-entirely-for-testing"),
        "no subject": make_token(None),
        "unknown user": make_token("no-such-user-" + uuid.uuid4().hex),
        "alg none": jwt.encode({"sub": name}, key=None, algorithm="none"),
    }
    for label, token in bad_tokens.items():
        response = client.get("/simulations", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401, f"{label}: expected 401, got {response.status_code}"

    # The same helper with the right key and subject is accepted, so the 401s above are for the right reason.
    assert client.get("/simulations", headers={"Authorization": f"Bearer {make_token(name)}"}).status_code == 200


def test_a_token_for_a_deleted_user_stops_working(client, make_user):
    account = make_user()
    headers = bearer(client, account)
    assert client.get("/simulations", headers=headers).status_code == 200

    db = SessionLocal()
    try:
        db.query(User).filter(User.id == account["id"]).delete()
        db.commit()
    finally:
        db.close()

    assert client.get("/simulations", headers=headers).status_code == 401


# ==========================================
# The reporting endpoint
# ==========================================
def test_insights_are_empty_for_a_user_with_no_runs(client, auth):
    assert client.get("/insights/event-types", headers=auth).json() == []


def test_insights_match_a_hand_calculation(client, auth):
    # One year at 5000/month and 12%: skipping month 2 loses 5000 grown for 11 months.
    payload = {"monthly_amount": 5000, "annual_return": 12, "years": 1}
    client.post("/simulate", json={**payload, "events": [{"type": "SKIP", "month": 2}]}, headers=auth)

    rows = client.get("/insights/event-types", headers=auth).json()
    assert len(rows) == 1

    skip = rows[0]
    loss = 5000 * 1.01**11                                # 5578.34
    ideal = 5000 * ((1.01**12 - 1) / 0.01) * 1.01
    ccr = 11 / 12
    score = 100 - (40 * (1 - ccr) + 60 * (loss / ideal))  # 91.44

    assert skip["event_type"] == "SKIP"
    assert skip["simulation_count"] == 1
    assert skip["avg_compounding_loss"] == pytest.approx(loss, abs=0.01)
    assert skip["avg_discipline_score"] == pytest.approx(score, abs=0.01)
    assert skip["loss_band"] == "Low"


def test_insights_count_runs_not_events(client, auth):
    """Two SKIPs inside one run are one run, so COUNT(DISTINCT s.id), not COUNT(*)."""
    payload = {"monthly_amount": 5000, "annual_return": 12, "years": 2}
    two_skips = [{"type": "SKIP", "month": 2}, {"type": "SKIP", "month": 3}]
    client.post("/simulate", json={**payload, "events": two_skips}, headers=auth)
    client.post("/simulate", json={**payload, "events": [{"type": "SKIP", "month": 4}]}, headers=auth)

    rows = {row["event_type"]: row for row in client.get("/insights/event-types", headers=auth).json()}
    assert rows["SKIP"]["simulation_count"] == 2


# ==========================================
# Monte Carlo endpoint
# ==========================================
MONTE_CARLO = {**PLAN, "events": [], "simulations": 200, "volatility": 0.15}


def test_monte_carlo_with_a_seed_returns_the_same_answer_twice(client):
    first = client.post("/monte-carlo", json={**MONTE_CARLO, "seed": 42}).json()
    second = client.post("/monte-carlo", json={**MONTE_CARLO, "seed": 42}).json()
    assert first == second


def test_monte_carlo_rejects_a_request_that_is_too_large(client):
    too_big = {**MONTE_CARLO, "years": 60, "simulations": 10000}
    response = client.post("/monte-carlo", json=too_big)
    assert response.status_code == 422
    assert "limit" in response.text

    # 5,000 simulations x 60 years sits exactly on the limit.
    assert client.post("/monte-carlo", json={**too_big, "simulations": 5000}).status_code == 200


def test_monte_carlo_validates_events_like_simulate_does(client):
    response = client.post("/monte-carlo", json={**MONTE_CARLO, "events": [{"type": "REDUCE", "month": 3}]})
    assert response.status_code == 422


# ==========================================
# Demo mode
# ==========================================
def test_demo_token_is_not_found_when_demo_mode_is_off(client, monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    assert client.post("/demo-token").status_code == 404


def test_demo_token_signs_in_the_demo_account_when_demo_mode_is_on(client, user, monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", True)
    monkeypatch.setattr(settings, "DEMO_USERNAME", user["username"])

    response = client.post("/demo-token")

    assert response.status_code == 200
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    assert client.get("/simulations", headers=headers).status_code == 200


def test_demo_token_is_unavailable_until_the_demo_account_exists(client, monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", True)
    monkeypatch.setattr(settings, "DEMO_USERNAME", f"missing-{uuid.uuid4().hex[:12]}")
    assert client.post("/demo-token").status_code == 503
