"""Drop and recreate the funds table so the sample catalogue is re-seeded.

Guarded by __main__ on purpose. Previously this ran its DROP at import time, so
merely importing the module - or letting an editor or test collector touch it -
destroyed the table.
"""

from database import engine
from models import Fund


def reset_funds() -> None:
    Fund.__table__.drop(engine, checkfirst=True)
    Fund.__table__.create(engine)
    print("Funds table reset. The catalogue is re-seeded on next application start.")


if __name__ == "__main__":
    reset_funds()
