"""
Wrapper for using PyTorch embedding models as UserEmbedding and ProductEmbedding.
"""
import torch
import numpy as np
from ml.embeddings.user_embeddings import UserEmbedding
from ml.embeddings.product_embeddings import ProductEmbedding
import logging

logger = logging.getLogger("uvicorn.error")

class TorchUserEmbedding(UserEmbedding):
    def __init__(self, model, num_users, embedding_dim):
        """
        Initialize the TorchUserEmbedding wrapper.

        Args:
            model: The PyTorch model that contains the user embedding layer.
            num_users: Number of users.
            embedding_dim: Dimension of the embeddings.
        """
        super().__init__(embedding_dim)
        self.model = model
        self.num_users = num_users
        # We assume the model has a method to get user embeddings
        # If not, we'll extract the user weight matrix
        if hasattr(model, 'get_user_embedding'):
            self.get_user_embedding = model.get_user_embedding
        elif hasattr(model, 'user_embedding'):
            self.user_embedding_layer = model.user_embedding
        else:
            # Try to find the user embedding layer by name
            for name, param in model.named_parameters():
                if 'user_emb' in name or 'user_embed' in name:
                    self.user_embedding_layer = param
                    break
            else:
                raise ValueError("Could not find user embedding layer in the model")

    def get_embedding(self, user_id):
        """
        Get the embedding for a user.

        Args:
            user_id: The user ID (can be string or int).

        Returns:
            The embedding as a numpy array.
        """
        # Convert user_id to index if it's a string like "user_123"
        if isinstance(user_id, str) and user_id.startswith("user_"):
            try:
                idx = int(user_id.split("_")[1])
            except ValueError:
                idx = hash(user_id) % self.num_users
        else:
            # Assume it's already an index or can be hashed to an index
            idx = int(user_id) if isinstance(user_id, int) else hash(user_id) % self.num_users

        # Clamp index to valid range
        idx = max(0, min(idx, self.num_users - 1))

        if hasattr(self, 'get_user_embedding'):
            embedding = self.get_user_embedding(idx)
        elif hasattr(self, 'user_embedding_layer'):
            embedding = self.user_embedding_layer[idx]
        else:
            # This should not happen
            raise RuntimeError("User embedding layer not found")

        # Ensure it's a numpy array
        if isinstance(embedding, torch.Tensor):
            embedding = embedding.detach().cpu().numpy()
        return embedding

    def get_embeddings(self, user_ids):
        """
        Get embeddings for a list of user IDs.

        Args:
            user_ids: List of user IDs.

        Returns:
            A numpy array of shape (len(user_ids), embedding_dim).
        """
        embeddings = []
        for user_id in user_ids:
            embeddings.append(self.get_embedding(user_id))
        return np.array(embeddings, dtype=np.float32)

class TorchProductEmbedding(ProductEmbedding):
    def __init__(self, model, num_products, embedding_dim):
        """
        Initialize the TorchProductEmbedding wrapper.

        Args:
            model: The PyTorch model that contains the product embedding layer.
            num_products: Number of products.
            embedding_dim: Dimension of the embeddings.
        """
        super().__init__(embedding_dim)
        self.model = model
        self.num_products = num_products
        # We assume the model has a method to get product embeddings
        # If not, we'll extract the product weight matrix
        if hasattr(model, 'get_product_embedding'):
            self.get_product_embedding = model.get_product_embedding
        elif hasattr(model, 'product_embedding'):
            self.product_embedding_layer = model.product_embedding
        else:
            # Try to find the product embedding layer by name
            for name, param in model.named_parameters():
                if 'product_emb' in name or 'product_embed' in name:
                    self.product_embedding_layer = param
                    break
            else:
                raise ValueError("Could not find product embedding layer in the model")

    def get_embedding(self, product_id):
        """
        Get the embedding for a product.

        Args:
            product_id: The product ID (can be string or int).

        Returns:
            The embedding as a numpy array.
        """
        # Convert product_id to index if it's a string like "product_123"
        if isinstance(product_id, str) and product_id.startswith("product_"):
            try:
                idx = int(product_id.split("_")[1])
            except ValueError:
                idx = hash(product_id) % self.num_products
        else:
            # Assume it's already an index or can be hashed to an index
            idx = int(product_id) if isinstance(product_id, int) else hash(product_id) % self.num_products

        # Clamp index to valid range
        idx = max(0, min(idx, self.num_products - 1))

        if hasattr(self, 'get_product_embedding'):
            embedding = self.get_product_embedding(idx)
        elif hasattr(self, 'product_embedding_layer'):
            embedding = self.product_embedding_layer[idx]
        else:
            # This should not happen
            raise RuntimeError("Product embedding layer not found")

        # Ensure it's a numpy array
        if isinstance(embedding, torch.Tensor):
            embedding = embedding.detach().cpu().numpy()
        return embedding

    def get_embeddings(self, product_ids):
        """
        Get embeddings for a list of product IDs.

        Args:
            product_ids: List of product IDs.

        Returns:
            A numpy array of shape (len(product_ids), embedding_dim).
        """
        embeddings = []
        for product_id in product_ids:
            embeddings.append(self.get_embedding(product_id))
        return np.array(embeddings, dtype=np.float32)