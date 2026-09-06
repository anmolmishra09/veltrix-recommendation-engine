"""
Product repository for database operations related to products.
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import Optional, List
from ..core import models
import logging

logger = logging.getLogger(__name__)

class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_product(self, product_id: int) -> Optional[models.Product]:
        """
        Get product by ID.
        """
        return self.db.query(models.Product).filter(models.Product.id == product_id).first()

    def get_product_by_external_id(self, external_id: str) -> Optional[models.Product]:
        """
        Get product by external ID (if applicable).
        In this model, we use the primary key as external ID.
        """
        return self.get_product(int(external_id)) if external_id.isdigit() else None

    def get_products_by_ids(self, product_ids: List[int]) -> List[models.Product]:
        """
        Get multiple products by their IDs.
        """
        if not product_ids:
            return []
        return self.db.query(models.Product).filter(models.Product.id.in_(product_ids)).all()

    def get_products_by_category(self, category: str, limit: int = 100) -> List[models.Product]:
        """
        Get products by category.
        """
        return self.db.query(models.Product).filter(
            models.Product.category == category
        ).limit(limit).all()

    def search_products(self, query: str, limit: int = 50) -> List[models.Product]:
        """
        Search products by name or description.
        """
        search_term = f"%{query}%"
        return self.db.query(models.Product).filter(
            or_(
                models.Product.name.ilike(search_term),
                models.Product.description.ilike(search_term)
            )
        ).limit(limit).all()

    def get_top_products_by_interactions(self, limit: int = 100) -> List[models.Product]:
        """
        Get top products by total interactions (views, clicks, purchases).
        """
        from ..core import models  # Avoid circular import
        return self.db.query(
            models.Product,
            func.count(models.Interaction.id).label('interaction_count')
        ).join(
            models.Interaction, models.Product.id == models.Interaction.product_id
        ).group_by(
            models.Product.id
        ).order_by(
            desc('interaction_count')
        ).limit(limit).all()

    def create_product(self, product: models.Product) -> models.Product:
        """
        Create a new product.
        """
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        logger.info(f"Created product ID {product.id}")
        return product

    def update_product(self, product_id: int, updates: dict) -> Optional[models.Product]:
        """
        Update a product.
        """
        product = self.get_product(product_id)
        if not product:
            return None
        for key, value in updates.items():
            if hasattr(product, key):
                setattr(product, key, value)
        self.db.commit()
        self.db.refresh(product)
        logger.info(f"Updated product ID {product.id}")
        return product

    def delete_product(self, product_id: int) -> bool:
        """
        Delete a product.
        """
        product = self.get_product(product_id)
        if not product:
            return False
        self.db.delete(product)
        self.db.commit()
        logger.info(f"Deleted product ID {product_id}")
        return True