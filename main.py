from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import List, Optional, Literal

from fastapi import FastAPI, Query, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import func, text
from sqlalchemy.orm import Session, selectinload

from config import settings
from database import engine, Base, get_db, SessionLocal
from models import Simulation, SimulationEvent, Fund, User
from auth import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_current_user,
)
from engine.simulation import SIPSimulator
from engine.friction import calculate_ccr, calculate_cld, calculate_discipline_score

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("sip_friction_api")


def seed_initial_data():
    """Seed the sample fund catalogue, and optionally one account.

    The account is only created when DEFAULT_ADMIN_PASSWORD is set. There is no
    fallback password, because a committed default would mean every deployment
    of this code ships with the same known credentials.
    """
    db = SessionLocal()
    try:
        if db.query(Fund).count() == 0:
            funds = [
                Fund(
                    name="Parag Parikh Flexi Cap Fund Direct",
                    category="Flexi Cap",
                    platform="All Platforms",
                    risk_level="Moderately High",
                    return_3y=21.4,
                    return_5y=24.1,
                    expense_ratio=0.60,
                    invest_url="https://amc.ppfas.com/"
                ),
                Fund(
                    name="Quant Small Cap Fund Direct",
                    category="Small Cap",
                    platform="All Platforms",
                    risk_level="Very High",
                    return_3y=34.2,
                    return_5y=41.5,
                    expense_ratio=0.77,
                    invest_url="https://quantmutual.com/"
                ),
                Fund(
                    name="HDFC Mid-Cap Opportunities Fund",
                    category="Mid Cap",
                    platform="All Platforms",
                    risk_level="High",
                    return_3y=28.5,
                    return_5y=26.2,
                    expense_ratio=0.81,
                    invest_url="https://www.hdfcfund.com/"
                ),
                Fund(
                    name="SBI Contra Fund Direct Growth",
                    category="Equity / Contra",
                    platform="All Platforms",
                    risk_level="Very High",
                    return_3y=31.2,
                    return_5y=29.4,
                    expense_ratio=0.68,
                    invest_url="https://www.sbimf.com/"
                ),
                Fund(
                    name="Nifty 50 Index Fund Direct",
                    category="Index",
                    platform="Groww",
                    risk_level="Moderate",
                    return_3y=14.2,
                    return_5y=15.6,
                    expense_ratio=0.20,
                    invest_url="https://groww.in/"
                )
            ]
            db.add_all(funds)
            db.commit()
            logger.info("Seeded sample fund catalogue (illustrative data, not live market data).")

        if not settings.DEFAULT_ADMIN_PASSWORD:
            if db.query(User).count() == 0:
                logger.warning(
                    "No accounts exist and DEFAULT_ADMIN_PASSWORD is unset, so none was created. "
                    "Set it in .env to seed a local account."
                )
        elif db.query(User).count() == 0:
            db.add(User(
                username=settings.DEFAULT_ADMIN_USER,
                hashed_password=get_password_hash(settings.DEFAULT_ADMIN_PASSWORD),
            ))
            db.commit()
            logger.info("Seeded account '%s'.", settings.DEFAULT_ADMIN_USER)
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        db.rollback()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    seed_initial_data()
    yield
    # Shutdown


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Simulates how skipped or reduced contributions affect the long-term outcome of a Systematic Investment Plan (SIP).",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# Schema Definitions
# ==========================================
class Event(BaseModel):
    type: Literal["SKIP", "REDUCE", "INCREASE", "PAUSE_RANGE", "STEP_UP"]
    month: Optional[int] = Field(None, ge=1, description="Target month for discrete events")
    factor: Optional[float] = Field(None, gt=0, description="Multiplier factor for reduction or increase")
    yearly_growth: Optional[float] = Field(None, ge=0, description="Annual growth rate for STEP_UP")
    start_month: Optional[int] = Field(None, ge=1, description="Start month for PAUSE_RANGE")
    end_month: Optional[int] = Field(None, ge=1, description="End month for PAUSE_RANGE")


class SimulationRequest(BaseModel):
    monthly_amount: float = Field(..., gt=0, description="Base monthly SIP contribution amount (INR)")
    annual_return: float = Field(..., gt=0, description="Expected annual rate of return percentage (e.g., 12 for 12%)")
    years: int = Field(..., gt=0, le=60, description="Investment horizon in years")
    events: List[Event] = Field(default_factory=list, description="List of investor behavioral/friction events")


class MonteCarloRequest(SimulationRequest):
    simulations: int = Field(1000, gt=0, le=10000, description="Number of stochastic simulation trials")
    volatility: float = Field(0.15, gt=0, le=1.0, description="Annualized portfolio standard deviation / volatility")


class ChartDataPoint(BaseModel):
    year: int
    ideal: float
    actual: float
    # The gap the chart shades between the two lines. Returned by the API rather
    # than derived in the browser so there is one definition of it.
    difference: float


class SimulationResponse(BaseModel):
    simulation_id: int
    ideal_value: float
    actual_value: float
    compounding_loss: float
    discipline_score: float
    ccr: float
    total_expected_contribution: float
    total_actual_contribution: float
    chart_data: List[ChartDataPoint]


class SimulationEventOut(BaseModel):
    type: str
    month: Optional[int] = None
    factor: Optional[float] = None
    yearly_growth: Optional[float] = None
    start_month: Optional[int] = None
    end_month: Optional[int] = None


class SimulationSummary(BaseModel):
    id: int
    created_at: datetime
    monthly_amount: float
    annual_return: float
    years: int
    ideal_value: float
    actual_value: float
    compounding_loss: float
    discipline_score: float
    ccr: float
    event_count: int


class SimulationDetail(SimulationSummary):
    events: List[SimulationEventOut]


class EventTypeInsight(BaseModel):
    event_type: str
    simulation_count: int
    avg_discipline_score: float
    avg_compounding_loss: float
    loss_band: str


class MonteCarloResponse(BaseModel):
    mean: float
    p10: float
    p50: float
    p90: float
    best_case: float
    worst_case: float


class FundOut(BaseModel):
    id: int
    name: str
    category: str
    platform: str
    risk_level: str
    return_3y: float
    return_5y: float
    expense_ratio: float
    invest_url: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


def _event_to_out(event: SimulationEvent) -> SimulationEventOut:
    return SimulationEventOut(
        type=event.event_type,
        month=event.month,
        factor=event.factor,
        yearly_growth=event.yearly_growth,
        start_month=event.start_month,
        end_month=event.end_month,
    )


# ==========================================
# Routes
# ==========================================
@app.get("/api", tags=["System"])
def read_root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs"
    }


@app.post("/token", response_model=Token, tags=["Auth"])
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/simulate", response_model=SimulationResponse, tags=["Simulation"])
def simulate_sip(
    request: SimulationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run a simulation and save it, with its friction events, for this user.

    The simulation row and all of its event rows are written in a single
    transaction. A run saved without the events that produced it could not be
    explained or reproduced later, so a partial write is worse than no write.
    """
    try:
        sim = SIPSimulator(
            monthly_amount=request.monthly_amount,
            annual_return=request.annual_return / 100.0,
            years=request.years
        )

        events_dict = [event.model_dump() for event in request.events]

        ideal, ideal_history = sim.calculate_ideal()
        actual, total_expected, total_actual, actual_history = sim.calculate_actual(events_dict)

        ccr = calculate_ccr(total_expected, total_actual)
        cld = calculate_cld(ideal, actual)
        cld_ratio = (cld / ideal) if ideal > 0 else 0.0
        discipline_score = calculate_discipline_score(ccr, cld_ratio)

        db_simulation = Simulation(
            user_id=current_user.id,
            monthly_amount=request.monthly_amount,
            annual_return=request.annual_return,
            years=request.years,
            ideal_value=ideal,
            actual_value=actual,
            compounding_loss=cld,
            discipline_score=discipline_score,
            ccr=ccr,
            events=[
                SimulationEvent(
                    event_type=event.type,
                    month=event.month,
                    factor=event.factor,
                    yearly_growth=event.yearly_growth,
                    start_month=event.start_month,
                    end_month=event.end_month,
                )
                for event in request.events
            ],
        )
        db.add(db_simulation)
        # One commit for the parent and every child row: they land together or
        # not at all.
        db.commit()
        db.refresh(db_simulation)

        chart_data = [
            ChartDataPoint(
                year=i_hist["year"],
                ideal=i_hist["ideal_value"],
                actual=a_hist["actual_value"],
                difference=round(i_hist["ideal_value"] - a_hist["actual_value"], 2),
            )
            for i_hist, a_hist in zip(ideal_history, actual_history)
        ]

        return SimulationResponse(
            simulation_id=db_simulation.id,
            ideal_value=ideal,
            actual_value=actual,
            compounding_loss=cld,
            discipline_score=discipline_score,
            ccr=ccr,
            total_expected_contribution=total_expected,
            total_actual_contribution=total_actual,
            chart_data=chart_data
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error executing SIP simulation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to calculate SIP simulation")


@app.get("/simulations", response_model=List[SimulationSummary], tags=["Simulation"])
def list_simulations(
    limit: int = Query(20, gt=0, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """This user's saved runs, newest first, with a count of friction events.

    A LEFT OUTER JOIN is used rather than an inner join so that a clean run -
    one with no friction events at all - still appears in the history with a
    count of zero. An inner join would silently hide exactly the baseline runs
    a user most wants to compare against.

    This is the query the composite index on (user_id, created_at DESC) exists
    to serve.
    """
    rows = (
        db.query(Simulation, func.count(SimulationEvent.id).label("event_count"))
        .outerjoin(SimulationEvent, SimulationEvent.simulation_id == Simulation.id)
        .filter(Simulation.user_id == current_user.id)
        .group_by(Simulation.id)
        .order_by(Simulation.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        SimulationSummary(
            id=simulation.id,
            created_at=simulation.created_at,
            monthly_amount=simulation.monthly_amount,
            annual_return=simulation.annual_return,
            years=simulation.years,
            ideal_value=simulation.ideal_value,
            actual_value=simulation.actual_value,
            compounding_loss=simulation.compounding_loss,
            discipline_score=simulation.discipline_score,
            ccr=simulation.ccr,
            event_count=event_count,
        )
        for simulation, event_count in rows
    ]


@app.get("/simulations/{simulation_id}", response_model=SimulationDetail, tags=["Simulation"])
def get_simulation(
    simulation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """One saved run with the friction events that produced it.

    The user_id filter is part of the lookup rather than a check afterwards, so
    requesting someone else's simulation id returns 404 instead of leaking that
    the row exists.
    """
    simulation = (
        db.query(Simulation)
        .options(selectinload(Simulation.events))
        .filter(Simulation.id == simulation_id, Simulation.user_id == current_user.id)
        .first()
    )

    if simulation is None:
        raise HTTPException(status_code=404, detail="Simulation not found")

    return SimulationDetail(
        id=simulation.id,
        created_at=simulation.created_at,
        monthly_amount=simulation.monthly_amount,
        annual_return=simulation.annual_return,
        years=simulation.years,
        ideal_value=simulation.ideal_value,
        actual_value=simulation.actual_value,
        compounding_loss=simulation.compounding_loss,
        discipline_score=simulation.discipline_score,
        ccr=simulation.ccr,
        event_count=len(simulation.events),
        events=[_event_to_out(event) for event in simulation.events],
    )


# Written as raw SQL rather than through the ORM. The ORM is the right tool for
# loading objects, but this returns an aggregate report that maps to no entity,
# and the SQL says what it does more plainly than the query-builder equivalent.
EVENT_TYPE_INSIGHTS_SQL = text("""
    SELECT e.event_type                                    AS event_type,
           COUNT(DISTINCT s.id)                            AS simulation_count,
           ROUND(AVG(s.discipline_score)::numeric, 2)      AS avg_discipline_score,
           ROUND(AVG(s.compounding_loss)::numeric, 2)      AS avg_compounding_loss,
           CASE
               WHEN AVG(s.compounding_loss) <  100000 THEN 'Low'
               WHEN AVG(s.compounding_loss) < 1000000 THEN 'Medium'
               ELSE                                        'High'
           END                                             AS loss_band
    FROM simulation_events e
    JOIN simulations s ON s.id = e.simulation_id
    WHERE s.user_id = :user_id
    GROUP BY e.event_type
    ORDER BY avg_discipline_score ASC
""")


@app.get("/insights/event-types", response_model=List[EventTypeInsight], tags=["Insights"])
def event_type_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Which kinds of friction cost this user the most, across all saved runs.

    COUNT(DISTINCT s.id) rather than COUNT(*): a single run can contain several
    events of the same type, which would otherwise be counted more than once.
    """
    rows = db.execute(EVENT_TYPE_INSIGHTS_SQL, {"user_id": current_user.id}).mappings().all()

    return [
        EventTypeInsight(
            event_type=row["event_type"],
            simulation_count=row["simulation_count"],
            avg_discipline_score=float(row["avg_discipline_score"]),
            avg_compounding_loss=float(row["avg_compounding_loss"]),
            loss_band=row["loss_band"],
        )
        for row in rows
    ]


@app.post("/monte-carlo", response_model=MonteCarloResponse, tags=["Simulation"])
def monte_carlo_simulation(request: MonteCarloRequest):
    try:
        sim = SIPSimulator(
            monthly_amount=request.monthly_amount,
            annual_return=request.annual_return / 100.0,
            years=request.years
        )

        events_dict = [event.model_dump() for event in request.events]

        result = sim.monte_carlo(
            events=events_dict,
            simulations=request.simulations,
            volatility=request.volatility
        )

        return MonteCarloResponse(**result)
    except Exception as e:
        logger.error(f"Error executing Monte Carlo simulation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to run Monte Carlo analysis")


@app.get("/funds", response_model=List[FundOut], tags=["Funds"])
def get_all_funds(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    try:
        return db.query(Fund).offset(skip).limit(limit).all()
    except Exception as e:
        logger.error(f"Error fetching funds: {e}")
        raise HTTPException(status_code=500, detail="Database query failed")


@app.get("/search-funds", response_model=List[FundOut], tags=["Funds"])
def search_funds(
    q: Optional[str] = Query(None, description="Search term for fund name"),
    risk: Optional[str] = Query(None, description="Risk level filter"),
    platform: Optional[str] = Query(None, description="Investment platform filter"),
    sort_by: Optional[str] = Query(None, description="Sort field: return_3y, return_5y, expense_ratio"),
    db: Session = Depends(get_db)
):
    """Filter the fund catalogue.

    When nothing matches, this returns an empty list. It previously fell back to
    the top five funds by 5-year return, which made the filters lie: selecting a
    platform with no funds returned unrelated funds as though they had matched.
    """
    try:
        query = db.query(Fund)

        if q:
            query = query.filter(Fund.name.ilike(f"%{q}%"))
        if risk and risk != "All":
            query = query.filter(Fund.risk_level.ilike(f"%{risk}%"))
        if platform and platform != "All Platforms":
            query = query.filter(Fund.platform.ilike(f"%{platform}%"))

        if sort_by == "return_3y":
            query = query.order_by(Fund.return_3y.desc())
        elif sort_by == "return_5y":
            query = query.order_by(Fund.return_5y.desc())
        elif sort_by == "expense_ratio":
            query = query.order_by(Fund.expense_ratio.asc())
        else:
            query = query.order_by(Fund.name.asc())

        return query.all()
    except Exception as e:
        logger.error(f"Error searching funds: {e}")
        raise HTTPException(status_code=500, detail="Search operation failed")


# Serve the built frontend, when one has been built.
#
# Mounted last and at "/" because a mount matches every path beneath it: placed
# earlier it would shadow the API routes above. The Dockerfile builds
# frontend/dist and copies it here, but nothing served it before this mount, so
# the container exposed only the JSON API.
_frontend_dist = Path(__file__).resolve().parent / "frontend" / "dist"
if _frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")
    logger.info("Serving built frontend from %s", _frontend_dist)
else:
    logger.info("No frontend build found at %s; running API only.", _frontend_dist)
