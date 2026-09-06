"""
Custom exceptions.
"""
from fastapi import HTTPException
from typing import Any, Dict, Optional

class RecommendationException(HTTPException):
    def __init__(self, status_code: int, detail: str, headers: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=status_code, detail=detail, headers=headers)

class UserNotFoundException(RecommendationException):
    def __init__(self, user_id: str):
        super().__init__(
            status_code=404,
            detail=f"User with ID '{user_id}' not found"
        )

class ProductNotFoundException(RecommendationException):
    def __init__(self, product_id: str):
        super().__init__(
            status_code=404,
            detail=f"Product with ID '{product_id}' not found"
        )

class ModelNotFoundException(RecommendationException):
    def __init__(self, model_name: str):
        super().__init__(
            status_code=404,
            detail=f"Model '{model_name}' not found"
        )

class InvalidInputException(RecommendationException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=400,
            detail=detail
        )