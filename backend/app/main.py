from fastapi import FastAPI

app = FastAPI()

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

@app.get("/api/")
async def root():
    return {"message": "Welcome to PayOS Backend API"}