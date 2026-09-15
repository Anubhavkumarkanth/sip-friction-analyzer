"""SQLAlchemy models.

The schema is deliberately relational: a user owns many simulations, and a
simulation owns many friction events. Before this, the three tables had no
foreign keys at all and the friction events sent to /simulate were used to build
the contribution schedule and then thrown away, so a saved run could not be
reproduced or even attributed to anyone.

CHECK constraints mirror guarantees the simulation engine already makes. The
engine clamps the discipline score to 0-100 and the CCR to 0-1; the database
enforces the same bounds so a future code change cannot quietly write a value
that the rest of the application would treat as impossible.
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
    """One saved run of the simulator.

    The inputs are stored alongside the results so a historical run is
    self-describing: without monthly_amount / annual_return / years, a saved
    row could not be explained or re-run later.
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
    """A single friction event belonging to a saved simulation.

    The columns are nullable because the event types genuinely use different
    fields: SKIP needs only a month, PAUSE_RANGE needs a start and end, STEP_UP
    needs a yearly growth rate. The CHECK constraints validate each field on its
    own terms rather than pretending every event has every attribute.
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

    Figures here are illustrative sample data used to exercise the UI. They are
    not live market data and must not be presented as such.
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


# Composite index supporting the history endpoint, whose query is
# "this user's simulations, newest first".
#
# user_id leads because it is the equality predicate that narrows the table to
# one user. created_at DESC follows so that, within a user, rows are already in
# the order the query asks for. The reverse order would be far less useful here:
# a B-tree seeks efficiently only on its leading column, and this query has no
# filter on created_at at all.
Index(
    "ix_simulations_user_created",
    Simulation.user_id,
    Simulation.created_at.desc(),
)
