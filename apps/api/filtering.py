"""
Filtering module for recommendation results.
"""
from typing import List, Tuple
import logging

logger = logging.getLogger("uvicorn.error")

class RecommendationFilter:
    def __init__(self, exclude_recently_purchased: bool = False, recently_purchased_window_seconds: int = 86400):
        """
        Initialize the filter.

        Args:
            exclude_recently_purchased: Whether to exclude products recently purchased by the user.
            recently_purchased_window_seconds: Time window in seconds to consider a purchase as recent.
        """
        self.exclude_recently_purchased = exclude_recently_purchased
        self.recently_purchased_window_seconds = recently_purchased_window_seconds
        # In a real implementation, we would load product availability, validity, etc. from a database or cache.
        # For now, we'll assume all products are available and valid.

    def filter(
        self,
        user_id: str,
        recommendations: List[Tuple[str, float]],
        # In a real implementation, we would pass in:
        # - product availability (from inventory service)
        # - product validity (e.g., not expired)
        # - user's recently purchased products (from event store)
        # - business rules (e.g., no more than 2 recommendations from the same category)
    ) -> List[Tuple[str, float]]:
        """
        Filter the recommendation list.

        Steps:
        1. Remove unavailable products (if we had inventory data)
        2. Remove invalid products (if we had validation data)
        3. Remove duplicate products (by product_id)
        4. Optionally remove recently purchased products
        5. Apply business rules (e.g., diversity, no more than N from same category)
        6. Return the filtered list.

        For now, we'll just remove duplicates and return the list.
        """
        # Remove duplicates by product_id (assuming the tuple is (product_id, score))
        seen = set()
        filtered = []
        for product_id, score in recommendations:
            if product_id not in seen:
                seen.add(product_id)
                filtered.append((product_id, score))
            else:
                logger.warning(f"Duplicate product_id {product_id} found in recommendations for user {user_id}")

        # TODO: Implement the other filtering steps when the data sources are available.

        return filtered