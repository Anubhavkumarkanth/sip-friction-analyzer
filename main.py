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

