from sqlalchemy import Column, Integer, Float, DateTime, String
from datetime import datetime

from database import Base

# -----------------------------
# User Table
# -----------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
class Simulation(Base):
    __tablename__ = "simulations"

    id = Column(Integer, primary_key=True, index=True)
    ideal_value = Column(Float)
    actual_value = Column(Float)
    compounding_loss = Column(Float)
    discipline_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


# -----------------------------
# Funds Table
# -----------------------------
class Fund(Base):
    __tablename__ = "funds"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    risk_level = Column(String, nullable=False)
    return_3y = Column(Float, nullable=False)
    return_5y = Column(Float, nullable=False)
    expense_ratio = Column(Float, nullable=False)
    invest_url = Column(String, nullable=False)