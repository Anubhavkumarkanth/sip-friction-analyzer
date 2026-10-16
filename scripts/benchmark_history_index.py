"""Reproduce the index measurement described in docs/index-evaluation.md.

It builds a synthetic data set (users, simulations and their events), then runs
the history lookup with and without the composite index
ix_simulations_user_created and prints the planner's actual timings.

Two queries are measured:

  simplified  the query the evaluation document describes: one user's runs,
              newest first, no join and no LIMIT.
  endpoint    the query GET /simulations really issues: the same filter, but with
              the LEFT JOIN on simulation_events, GROUP BY and LIMIT 20.

Usage (from the repository root):

    python scripts/benchmark_history_index.py \\
        --database-url postgresql+psycopg2://postgres@localhost:5432/sip_bench

The database name must end in _bench. The script empties the users and
simulations tables before seeding, so it refuses anything else rather than risk
a database someone uses. Create one with: createdb sip_bench

The data is random but seeded, so the same --seed gives the same rows. Timings
still vary with the machine and with what else is running; the script repeats
each query and reports the median, the fastest run and the 90th percentile.
"""

import argparse
import json
import os
import platform
import random
import statistics
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

EVENT_TYPES = ["SKIP", "REDUCE", "PAUSE_RANGE", "STEP_UP", "INCREASE"]
INDEX_NAME = "ix_simulations_user_created"

SIMPLIFIED_SQL = "SELECT * FROM simulations WHERE user_id = :uid ORDER BY created_at DESC"
ENDPOINT_SQL = """
SELECT simulations.*, count(simulation_events.id) AS event_count
FROM simulations
LEFT OUTER JOIN simulation_events ON simulation_events.simulation_id = simulations.id
WHERE simulations.user_id = :uid
GROUP BY simulations.id
ORDER BY simulations.created_at DESC
LIMIT 20
"""


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--database-url", required=True, help="SQLAlchemy URL of a database named *_bench")
    parser.add_argument("--rows", type=int, default=20000, help="simulations to insert (default 20000)")
    parser.add_argument("--users", type=int, default=200, help="distinct users (default 200)")
    parser.add_argument("--runs", type=int, default=40, help="timed repetitions per query and state (default 40)")
    parser.add_argument("--seed", type=int, default=42, help="seed for the synthetic data (default 42)")
    parser.add_argument("--user-id", type=int, default=42, help="the user whose history is queried (default 42)")
    parser.add_argument("--json", dest="json_out", help="also write the results to this JSON file")
    return parser.parse_args()


def synthetic_rows(rows, users, seed):
    """Deterministic fake simulations and events. Insertion order is shuffled in time."""
    rng = random.Random(seed)
    newest = datetime(2026, 10, 1, tzinfo=timezone.utc)
    simulations, events = [], []
    for sim_id in range(1, rows + 1):
        years = 1 + int(rng.random() * 30)
        monthly = round(1000 + rng.random() * 49000, 2)
        ideal = round(monthly * years * 12 * (1.5 + rng.random()), 2)
        loss = round(ideal * rng.random() * 0.3, 2)
        simulations.append({
            "id": sim_id,
            "user_id": 1 + int(rng.random() * users),
            "monthly_amount": monthly,
            "annual_return": round(6 + rng.random() * 12, 2),
            "years": years,
            "ideal_value": ideal,
            "actual_value": round(ideal - loss, 2),
            "compounding_loss": loss,
            "discipline_score": round(40 + rng.random() * 60, 2),
            "ccr": round(0.6 + rng.random() * 0.4, 4),
            "created_at": newest - timedelta(seconds=int(rng.random() * 730 * 86400)),
        })
        if rng.random() < 0.7:
            for _ in range(1 + int(rng.random() * 3)):
                events.append({
                    "simulation_id": sim_id,
                    "event_type": rng.choice(EVENT_TYPES),
                    "month": 1 + int(rng.random() * years * 12),
                })
    return simulations, events


def plan_nodes(plan):
    """Every (node type, index name) in a plan tree, outermost first."""
    found = [(plan["Node Type"], plan.get("Index Name"))]
    for child in plan.get("Plans", []):
        found.extend(plan_nodes(child))
    return found


def explain(connection, text, sql, uid):
    row = connection.execute(text("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + sql), {"uid": uid}).scalar()
    document = row[0] if isinstance(row, list) else json.loads(row)[0]
    return document["Execution Time"], document["Planning Time"], document["Plan"]


def measure(connection, text, sql, uid, runs, warmups=5):
    for _ in range(warmups):
        explain(connection, text, sql, uid)
    executions, plannings, last_plan = [], [], None
    for _ in range(runs):
        execution, planning, last_plan = explain(connection, text, sql, uid)
        executions.append(execution)
        plannings.append(planning)
    executions.sort()
    return {
        "median_ms": round(statistics.median(executions), 3),
        "min_ms": round(executions[0], 3),
        "p90_ms": round(executions[int(0.9 * (len(executions) - 1))], 3),
        "planning_median_ms": round(statistics.median(plannings), 3),
        "plan_nodes": [f"{node} ({index})" if index else node for node, index in plan_nodes(last_plan)],
        "rows_scanned_removed": last_plan.get("Rows Removed by Filter"),
    }


def main():
    args = parse_args()

    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import make_url

    database = make_url(args.database_url).database or ""
    if not database.endswith("_bench"):
        sys.exit(
            f"Refusing to run: the database is '{database}'. "
            "This script empties tables, so the name must end in _bench."
        )

    # config.py reads DATABASE_URL once at import time, so set it before importing the models.
    os.environ["DATABASE_URL"] = args.database_url
    from database import Base
    import models  # noqa: F401  (registers the tables on Base.metadata)

    engine = create_engine(args.database_url)
    Base.metadata.create_all(engine)

    simulations, events = synthetic_rows(args.rows, args.users, args.seed)

    with engine.begin() as connection:
        connection.execute(text("TRUNCATE simulations, users RESTART IDENTITY CASCADE"))
        connection.execute(
            text("INSERT INTO users (username, hashed_password) "
                 "SELECT 'bench-user-' || g, 'not-a-real-hash' FROM generate_series(1, :n) g"),
            {"n": args.users},
        )
        for start in range(0, len(simulations), 2000):
            connection.execute(
                text("INSERT INTO simulations (id, user_id, monthly_amount, annual_return, years, ideal_value, "
                     "actual_value, compounding_loss, discipline_score, ccr, created_at) VALUES "
                     "(:id, :user_id, :monthly_amount, :annual_return, :years, :ideal_value, :actual_value, "
                     ":compounding_loss, :discipline_score, :ccr, :created_at)"),
                simulations[start:start + 2000],
            )
        for start in range(0, len(events), 2000):
            connection.execute(
                text("INSERT INTO simulation_events (simulation_id, event_type, month) "
                     "VALUES (:simulation_id, :event_type, :month)"),
                events[start:start + 2000],
            )
        connection.execute(text("SELECT setval(pg_get_serial_sequence('simulations', 'id'), :n)"), {"n": args.rows})

    results = {}
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        version = connection.execute(text("SELECT version()")).scalar()
        matching = connection.execute(
            text("SELECT count(*) FROM simulations WHERE user_id = :uid"), {"uid": args.user_id}
        ).scalar()

        for state in ("without index", "with index"):
            connection.execute(text(f"DROP INDEX IF EXISTS {INDEX_NAME}"))
            if state == "with index":
                connection.execute(text(f"CREATE INDEX {INDEX_NAME} ON simulations (user_id, created_at DESC)"))
            connection.execute(text("VACUUM ANALYZE users, simulations, simulation_events"))
            results[state] = {
                "simplified": measure(connection, text, SIMPLIFIED_SQL, args.user_id, args.runs),
                "endpoint": measure(connection, text, ENDPOINT_SQL, args.user_id, args.runs),
            }

        # Leave the database as the application defines it.
        connection.execute(text(f"CREATE INDEX IF NOT EXISTS {INDEX_NAME} ON simulations (user_id, created_at DESC)"))

    report = {
        "environment": {
            "postgres": version.split(" on ")[0],
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "data": {
            "simulations": args.rows, "events": len(events), "users": args.users, "seed": args.seed,
            "queried_user_id": args.user_id, "rows_for_that_user": matching,
        },
        "runs_per_measurement": args.runs,
        "results": results,
    }

    print(json.dumps(report["environment"], indent=2))
    print(json.dumps(report["data"], indent=2))
    print(f"\nExecution time in ms, {args.runs} runs after warm-up (median / fastest / p90):\n")
    print("| query | state | median | fastest | p90 | plan |")
    print("|---|---|---|---|---|---|")
    for query in ("simplified", "endpoint"):
        for state in ("without index", "with index"):
            r = results[state][query]
            print(f"| {query} | {state} | {r['median_ms']} | {r['min_ms']} | {r['p90_ms']} | "
                  f"{' > '.join(r['plan_nodes'])} |")
    for query in ("simplified", "endpoint"):
        before, after = results["without index"][query]["median_ms"], results["with index"][query]["median_ms"]
        print(f"\n{query}: median {before} ms -> {after} ms ({before / after:.1f}x)")

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
