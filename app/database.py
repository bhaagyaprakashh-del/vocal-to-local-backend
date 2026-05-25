from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Render automatically injects your secret string into the DATABASE_URL environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

# Quick format correction if Render gives a 'postgres://' string instead of 'postgresql://'
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to open and close database connections cleanly inside API calls
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
