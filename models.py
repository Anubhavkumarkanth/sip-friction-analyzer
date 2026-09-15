"""Database tables.

A user owns many simulations; a simulation owns many friction events. The tables
previously had no foreign keys at all, and the events sent to /simulate were used
to build the contribution schedule and then discarded, so a saved run could not
be reproduced or attributed to anyone.

The CHECK constraints mirror bounds the engine already enforces in code. Having
them in the database too means a future change cannot quietly write a discipline
score of 150.
"""

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    simulations = relationship(
        "Simulation",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Simulation(Base):
    """One saved run.

    Inputs are stored next to the results so an old run can still be explained or
    re-run; without them the row is just four numbers.
    """

    __tablename__ = "simulations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Inputs
    monthly_amount = Column(Float, nullable=False)
    annual_return = Column(Float, nullable=False)
    years = Column(Integer, nullable=False)

    # Results
    ideal_value = Column(Float, nullable=False)
    actual_value = Column(Float, nullable=False)
    compounding_loss = Column(Float, nullable=False)
    discipline_score = Column(Float, nullable=False)
    ccr = Column(Float, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="simulations")
    events = relationship(
        "SimulationEvent",
        back_populates="simulation",
        cascade="all, delete-orphan",
        order_by="SimulationEvent.id",
    )

    __table_args__ = (
        CheckConstraint(
            "discipline_score >= 0 AND discipline_score <= 100",
            name="ck_simulations_discipline_score_range",
        ),
        CheckConstraint("ccr >= 0 AND ccr <= 1", name="ck_simulations_ccr_range"),
        CheckConstraint("monthly_amount > 0", name="ck_simulations_monthly_amount_positive"),
        CheckConstraint("years > 0", name="ck_simulations_years_positive"),
        CheckConstraint("compounding_loss >= 0", name="ck_simulations_loss_non_negative"),
    )


class SimulationEvent(Base):
    """One friction event belonging to a simulation.

    Most columns are nullable because the event types use different fields: SKIP
    needs only a month, PAUSE_RANGE a start and end, STEP_UP a growth rate. The
    CHECK constraints validate each field on its own terms instead of pretending
    every event has every attribute.
    """

    __tablename__ = "simulation_events"

    id = Column(Integer, primary_key=True, index=True)
    simulation_id = Column(
        Integer,
        ForeignKey("simulations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    event_type = Column(String(20), nullable=False)
    month = Column(Integer)
    factor = Column(Float)
    yearly_growth = Column(Float)
    start_month = Column(Integer)
    end_month = Column(Integer)

    simulation = relationship("Simulation", back_populates="events")

    __table_args__ = (
        CheckConstraint(
            "event_type IN ('SKIP', 'REDUCE', 'INCREASE', 'PAUSE_RANGE', 'STEP_UP')",
            name="ck_simulation_events_type",
        ),
        CheckConstraint("month IS NULL OR month >= 1", name="ck_simulation_events_month"),
        CheckConstraint("factor IS NULL OR factor > 0", name="ck_simulation_events_factor"),
        CheckConstraint(
            "yearly_growth IS NULL OR yearly_growth >= 0",
            name="ck_simulation_events_growth",
        ),
        # A pause that ends before it starts is not a valid range.
        CheckConstraint(
            "start_month IS NULL OR end_month IS NULL OR end_month >= start_month",
            name="ck_simulation_events_month_range",
        ),
    )


class Fund(Base):
    """Reference data for the fund comparison screens.

    Sample figures for exercising the UI. Not live market data.
    """

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

    __table_args__ = (
        CheckConstraint("expense_ratio >= 0", name="ck_funds_expense_ratio_non_negative"),
    )


# Supports the history query: one user's simulations, newest first.
#
# user_id leads because it is the equality predicate that narrows the table.
# created_at follows so rows come back roughly in the order asked for. The
# reverse order would be near useless: a B-tree seeks only on its leading
# column, and this query never filters on created_at.
# Captured plans are in docs/index-evaluation.md.
Index(
    "ix_simulations_user_created",
    Simulation.user_id,
    Simulation.created_at.desc(),
)
