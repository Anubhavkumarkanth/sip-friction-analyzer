from contextlib import asynccontextmanager
from datetime import timedelta
import logging
from typing import List, Optional, Literal

from fastapi import FastAPI, Query, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from config import settings
from database import engine, Base, get_db, SessionLocal
from models import Simulation, Fund, User
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
    """Seeds baseline fund catalog and default administrator user if empty."""
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
            logger.info("Successfully seeded fund catalog.")

        if db.query(User).count() == 0:
            admin_user = User(
                username=settings.DEFAULT_ADMIN_USER,
                hashed_password=get_password_hash(settings.DEFAULT_ADMIN_PASSWORD)
            )
            db.add(admin_user)
            db.commit()
            logger.info("Seeded default admin user.")
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
    description="Financial simulation engine analyzing compounding loss and discipline degradation in Systematic Investment Plans (SIP).",
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


class SimulationResponse(BaseModel):
    ideal_value: float
    actual_value: float
    compounding_loss: float
    discipline_score: float
    ccr: float
    total_expected_contribution: float
    total_actual_contribution: float
    chart_data: List[ChartDataPoint]


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


# ==========================================
# Routes
# ==========================================
@app.get("/", tags=["System"])
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
def simulate_sip(request: SimulationRequest, db: Session = Depends(get_db)):
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

        # Persist simulation log
        db_simulation = Simulation(
            ideal_value=ideal,
            actual_value=actual,
            compounding_loss=cld,
            discipline_score=discipline_score
        )
        db.add(db_simulation)
        db.commit()

        chart_data = [
            ChartDataPoint(
                year=i_hist["year"],
                ideal=i_hist["ideal_value"],
                actual=a_hist["actual_value"]
            )
            for i_hist, a_hist in zip(ideal_history, actual_history)
        ]

        return SimulationResponse(
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
        logger.error(f"Error executing SIP simulation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to calculate SIP simulation")


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
    try:
        base_query = db.query(Fund)

        # 1. Strict filtering
        query = base_query
        if q:
            query = query.filter(Fund.name.ilike(f"%{q}%"))
        if risk and risk != "All":
            query = query.filter(Fund.risk_level.ilike(f"%{risk}%"))
        if platform and platform != "All Platforms":
            query = query.filter(Fund.platform.ilike(f"%{platform}%"))

        results = query.all()

        # 2. Relaxed fallback if strict filter returns empty
        if not results and q:
            results = base_query.filter(Fund.name.ilike(f"%{q}%")).all()

        # 3. Final default fallback
        if not results:
            results = base_query.order_by(Fund.return_5y.desc()).limit(5).all()

        # Sorting
        if sort_by == "return_3y":
            results = sorted(results, key=lambda x: x.return_3y, reverse=True)
        elif sort_by == "return_5y":
            results = sorted(results, key=lambda x: x.return_5y, reverse=True)
        elif sort_by == "expense_ratio":
            results = sorted(results, key=lambda x: x.expense_ratio)

        return results
    except Exception as e:
        logger.error(f"Error searching funds: {e}")
        raise HTTPException(status_code=500, detail="Search operation failed")