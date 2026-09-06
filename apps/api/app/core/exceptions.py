"""
Custom exceptions for the recommendation platform.
"""
class UserNotFoundException(Exception):
    """Raised when a user is not found in the system."""
    def __init__(self, user_id: str):
        self.user_id = user_id
        super().__init__(f"User not found: {user_id}")

class ProductNotFoundException(Exception):
    """Raised when a product is not found in the system."""
    def __init__(self, product_id: str):
        self.product_id = product_id
        super().__init__(f"Product not found: {product_id}")

class RecommendationException(Exception):
    """Base exception for recommendation-related errors."""
    pass

class ModelNotFoundException(Exception):
    """Raised when a model is not found."""
    def __init__(self, model_name: str):
        self.model_name = model_name
        super().__init__(f"Model not found: {model_name}")

class FeatureStoreException(Exception):
    """Raised when there is an error with the feature store."""
    pass