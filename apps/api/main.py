"""
FastAPI application for the recommendation service.
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Tuple
from .recommender import Recommender
import logging
import uuid

app = FastAPI(title="Recommendation Service")
recommender = Recommender()
logger = logging.getLogger("uvicorn.error")

class RecommendationRequest(BaseModel):
    user_id: str
    k: int = 10
    candidate_generator: str = "embedding"  # or "popularity"

class RecommendationResponse(BaseModel):
    recommendations: List[Tuple[str, float]]

class ErrorResponse(BaseModel):
    code: str
    message: str
    request_id: str

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = str(uuid.uuid4())
    logger.error(f"Request ID: {request_id} - Exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            code="INTERNAL_SERVER_ERROR",
            message="An internal server error occurred",
            request_id=request_id
        ).dict()
    )

@app.post("/recommend", response_model=RecommendationResponse)
def get_recommendations(request: RecommendationRequest):
    try:
        recommendations = recommender.recommend(
            user_id=request.user_id,
            k=request.k,
            candidate_generator=request.candidate_generator
        )
        return {"recommendations": recommendations}
    except Exception as e:
        # This will be caught by the global exception handler
        raise e

@app.get("/health")
def health_check():
    return {"status": "healthy"}