from fastapi import FastAPI, Query, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
import logging
from datetime import timedelta

from engine.simulation import SIPSimulator
from engine.friction import calculate_ccr, calculate_cld, calculate_discipline_score
from database import engine, SessionLocal, Base
from models import Simulation, Fund, User
from auth import authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_db, get_current_user

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

# ----------------------------------
# Request Models
# ----------------------------------
class Event(BaseModel):
    type: Literal["SKIP", "REDUCE", "INCREASE", "PAUSE_RANGE", "STEP_UP"]
    month: Optional[int] = Field(None, ge=1)
    factor: Optional[float] = Field(None, gt=0)
    yearly_growth: Optional[float] = Field(None, gt=0)
    start_month: Optional[int] = Field(None, ge=1)
    end_month: Optional[int] = Field(None, ge=1)

class SimulationRequest(BaseModel):
    monthly_amount: float = Field(..., gt=0)
    annual_return: float = Field(..., gt=0)
    years: int = Field(..., gt=0)
    events: List[Event] = []

class MonteCarloRequest(SimulationRequest):
    simulations: int = Field(1000, gt=0, le=5000)
    volatility: float = Field(0.15, gt=0)


# ----------------------------------
# Auth Routes
# ----------------------------------
@app.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# ----------------------------------
# Deterministic Simulation
# ----------------------------------
@app.post("/simulate")
def simulate_sip(request: SimulationRequest, db: Session = Depends(get_db)):
    try:
        sim = SIPSimulator(
            monthly_amount=request.monthly_amount,
            annual_return=request.annual_return / 100,  # Convert from % to decimal
            years=request.years
        )

        events_dict = [event.model_dump() for event in request.events]

        ideal, ideal_history = sim.calculate_ideal()
        actual, total_expected, total_actual, actual_history = sim.calculate_actual(events_dict)

        ccr = calculate_ccr(total_expected, total_actual)
        cld = calculate_cld(ideal, actual)
        cld_ratio = cld / ideal if ideal != 0 else 0
        discipline_score = calculate_discipline_score(ccr, cld_ratio)

        db_simulation = Simulation(
            ideal_value=ideal,
            actual_value=actual,
            compounding_loss=cld,
            discipline_score=discipline_score
        )
        db.add(db_simulation)
        db.commit()
        
        chart_data = []
        for i_hist, a_hist in zip(ideal_history, actual_history):
            chart_data.append({
                "year": i_hist["year"],
                "ideal": i_hist["ideal_value"],
                "actual": a_hist["actual_value"]
            })

        return {
            "ideal_value": ideal,
            "actual_value": actual,
            "compounding_loss": cld,
            "discipline_score": discipline_score,
            "ccr": ccr,
            "total_expected_contribution": total_expected,
            "total_actual_contribution": total_actual,
            "chart_data": chart_data
        }
    except Exception as e:
        logger.error(f"Error in simulate_sip: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# ----------------------------------
# Monte Carlo Simulation
# ----------------------------------
@app.post("/monte-carlo")
def monte_carlo_simulation(request: MonteCarloRequest):
    try:
        sim = SIPSimulator(
            monthly_amount=request.monthly_amount,
            annual_return=request.annual_return / 100,  # Convert from % to decimal
            years=request.years
        )

        events_dict = [event.model_dump() for event in request.events]

        result = sim.monte_carlo(
            events=events_dict,
            simulations=request.simulations,
            volatility=request.volatility
        )

        return result
    except Exception as e:
        logger.error(f"Error in monte_carlo_simulation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# ----------------------------------
# Funds - Get All
# ----------------------------------
@app.get("/funds")
def get_all_funds(db: Session = Depends(get_db)):
    try:
        funds = db.query(Fund).all()
        return funds
    except Exception as e:
        logger.error(f"Error in get_all_funds: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# ----------------------------------
# Smart Search (AI-like fallback)
# ----------------------------------
@app.get("/search-funds")
def search_funds(
    q: Optional[str] = Query(None),
    risk: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    try:
        base_query = db.query(Fund)

        # 1️⃣ Strict Filtering
        query = base_query

        if q:
            query = query.filter(Fund.name.ilike(f"%{q}%"))

        if risk:
            query = query.filter(Fund.risk_level.ilike(f"%{risk}%"))

        if platform:
            query = query.filter(Fund.platform.ilike(f"%{platform}%"))

        results = query.all()

        # 2️⃣ Fallback: Remove risk & platform if empty
        if not results:
            fallback_query = base_query

            if q:
                fallback_query = fallback_query.filter(Fund.name.ilike(f"%{q}%"))

            results = fallback_query.all()

        # 3️⃣ Final fallback: Show Top 3 by performance
        if not results:
            results = base_query.order_by(Fund.return_5y.desc()).limit(3).all()

        # Sorting (applied on final result)
        if sort_by:
            if sort_by == "return_3y":
                results.sort(key=lambda x: x.return_3y, reverse=True)
            elif sort_by == "return_5y":
                results.sort(key=lambda x: x.return_5y, reverse=True)
            elif sort_by == "expense_ratio":
                results.sort(key=lambda x: x.expense_ratio)

        return results
    except Exception as e:
        logger.error(f"Error in search_funds: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# ----------------------------------
# Seed Data
# ----------------------------------
@app.on_event("startup")
def seed_data():
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
                    expense_ratio=0.6,
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
                    name="Nifty 50 Index Fund",
                    category="Index",
                    platform="Groww",
                    risk_level="Moderate",
                    return_3y=14.2,
                    return_5y=15.6,
                    expense_ratio=0.2,
                    invest_url="https://groww.in/"
                )
            ]
            db.add_all(funds)
            db.commit()
            
        # Create a default test user if none exists
        from auth import get_password_hash
        if db.query(User).count() == 0:
            test_user = User(
                username="testuser",
                hashed_password=get_password_hash("password123")
            )
            db.add(test_user)
            db.commit()
            
    except Exception as e:
        logger.error(f"Error seeding data: {str(e)}")
    finally:
        db.close()