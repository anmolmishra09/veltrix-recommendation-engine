"""
Products endpoint.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, Optional
import logging

from ..core.database import SessionLocal, get_db
from sqlalchemy.orm import Session
from ..core.exceptions import ProductNotFoundException

logger = logging.getLogger(__name__)

router = APIRouter()

class ProductResponse(BaseModel):
    id: Any
    name: str
    category: Optional[str] = None
    subcategory: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    brand: Optional[str] = None
    inventory: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: Any,
    db: Session = Depends(get_db)
):
    """
    Get a product by ID.
    """
    # TODO: Implement actual database query
    # For now, we'll return a mock product
    logger.info(f"Fetching product {product_id}")
    # Mock product
    return ProductResponse(
        id=product_id,
        name=f"Product {product_id}",
        category="Electronics",
        subcategory="Gadgets",
        price=99.99,
        description="A sample product",
        brand="BrandX",
        inventory=100,
        metadata={"color": "black"}
    )

@router.get("/")
def get_products(limit: int = 100):
    """
    Get a list of products (for debugging).
    """
    # TODO: Implement actual database query
    return [{"id": i, "name": f"Product {i}"} for i in range(1, limit+1)]