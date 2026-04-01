from database import engine, SessionLocal
from models import Fund, Base

# Drop and recreate only the funds table to force a re-seed
Fund.__table__.drop(engine)
Fund.__table__.create(engine)

print("Funds table reset. Uvicorn will seed new data on next reload.")
