from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Vocal to Local API")

@app.get("/")
def read_root():
    return {"status": "healthy", "message": "Welcome to Vocal to Local API"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
