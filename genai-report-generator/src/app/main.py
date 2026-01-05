from fastapi import FastAPI
from src.app.core.logger import logger

app = FastAPI(title="GenAI Report Generator API")

@app.on_event("startup")
async def startup_event():
    logger.info("Application is starting...")

@app.get("/health")
def health_check():
    return {"status": "active", "module": "genai-reporter"}
