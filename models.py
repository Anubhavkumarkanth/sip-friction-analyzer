from sqlalchemy import Column, Integer, Float, DateTime, String
from datetime import datetime

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Simulation(Base):
    __tablename__ = "simulations"

    id = Column(Integer, primary_key=True, index=True)
    ideal_value = Column(Float, nullable=False)
    actual_value = Column(Float, nullable=False)
    compounding_loss = Column(Float, nullable=False)
    discipline_score = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Fund(Base):
    __tablename__ = "funds"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)
    category = Column(String(100), index=True, nullable=False)
    platform = Column(String(100), index=True, nullable=False)
    risk_level = Column(String(50), index=True, nullable=False)
    return_3y = Column(Float, nullable=False)
    return_5y = Column(Float, nullable=False)
    expense_ratio = Column(Float, nullable=False)
    invest_url = Column(String(500), nullable=False)