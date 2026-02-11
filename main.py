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


