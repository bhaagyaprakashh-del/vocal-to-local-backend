from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.database import engine, Base, get_db

# This line auto-creates the tables inside PostgreSQL if they do not exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Vocal to Local API")

@app.get("/")
def read_root():
    return {"status": "healthy", "message": "Welcome to Vocal to Local API"}

# Quick test endpoint to verify database connection works over HTTP
@app.get("/db-test")
def test_db_connection(db: Session = Depends(get_db)):
    return {"status": "success", "message": "Database tables loaded and communicating cleanly!"}
