"""
Recommendation service that uses the trained models and feature store.
"""
import pandas as pd
import torch
import numpy as np
from feast import FeatureStore
from ml.recommendation.candidate_generation.embedding_based import EmbeddingBasedCandidateGenerator
from ml.recommendation.candidate_generation.popularity import PopularityCandidateGenerator
from .filtering import RecommendationFilter
from .model_loader import ModelLoader
from .embedding_wrapper import TorchUserEmbedding, TorchProductEmbedding

class Recommender:
    def __init__(self, feature_store_path="./feast_repository"):
        self.feature_store = FeatureStore(repo_path=feature_store_path)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_loader = ModelLoader()
        self.embedding_model = self.model_loader.get_embedding_model()
        self.ranking_model = self.model_loader.get_ranking_model()

        # We need to know the number of users and products
        # We'll get this from the feature store or from the model metadata
        # For now, we'll hardcode or load from a file
        self.num_users = 1000  # TODO: make dynamic
        self.num_products = 100  # TODO: make dynamic
        self.embedding_dim = 64  # Should match the model

        # Create wrappers for the embedding model to be used by the candidate generator
        self.user_embedding = TorchUserEmbedding(
            model=self.embedding_model,
            num_users=self.num_users,
            embedding_dim=self.embedding_dim
        )
        self.product_embedding = TorchProductEmbedding(
            model=self.embedding_model,
            num_products=self.num_products,
            embedding_dim=self.embedding_dim
        )

        # Initialize candidate generators
        self.embedding_candidate_generator = EmbeddingBasedCandidateGenerator(
            user_embedding=self.user_embedding,
            product_embedding=self.product_embedding
        )
        # For popularity, we'll compute from the product features (total interactions)
        # We'll load the product features and compute a popularity score
        product_features_df = self.feature_store.get_historical_features(
            entity_df=pd.DataFrame({
                "product_id": list(range(self.num_products))
            }),
            features=[
                "product_features:total_views",
                "product_features:total_clicks",
                "product_features:total_purchases"
            ]
        ).to_df()
        # Compute popularity as a combination of views, clicks, and purchases
        product_features_df['popularity_score'] = (
            product_features_df['product_features:total_views'] +
            2 * product_features_df['product_features:total_clicks'] +
            3 * product_features_df['product_features:total_purchases']
        )
        self.popularity_candidate_generator = PopularityCandidateGenerator(
            product_features_df[['product_id', 'popularity_score']]
        )

        # Initialize the filter
        self.filter = RecommendationFilter()

    def get_user_features(self, user_id):
        """
        Get user features from the feature store.
        """
        user_features = self.feature_store.get_online_features(
            features=[
                "user_features:total_views",
                "user_features:total_clicks",
                "user_features:total_purchases",
                "user_features:total_spent"
            ],
            entity_rows=[{"user_id": user_id}]
        ).to_dict()
        # Convert to array in the correct order
        feature_array = np.array([
            user_features["user_features:total_views"][0],
            user_features["user_features:total_clicks"][0],
            user_features["user_features:total_purchases"][0],
            user_features["user_features:total_spent"][0]
        ])
        return feature_array

    def get_product_features(self, product_id):
        """
        Get product features from the feature store.
        """
        product_features = self.feature_store.get_online_features(
            features=[
                "product_features:total_views",
                "product_features:total_clicks",
                "product_features:total_purchases"
            ],
            entity_rows=[{"product_id": product_id}]
        ).to_dict()
        feature_array = np.array([
            product_features["product_features:total_views"][0],
            product_features["product_features:total_clicks"][0],
            product_features["product_features:total_purchases"][0]
        ])
        return feature_array

    def recommend(self, user_id, k=10, candidate_generator='embedding'):
        """
        Generate top-k recommendations for a user.
        """
        # Get user features
        user_features = self.get_user_features(user_id)
        user_features_tensor = torch.FloatTensor(user_features).unsqueeze(0).to(self.device)

        # Generate candidates
        if candidate_generator == 'embedding':
            candidates = self.embedding_candidate_generator.generate_candidates(
                user_id,  # Now we pass the user_id string directly
                k=100  # get more candidates than needed for ranking
            )
        else:  # popularity
            candidates = self.popularity_candidate_generator.generate_candidates(
                user_id,
                k=100
            )

        candidate_product_ids = [cid for cid, _ in candidates]

        # Get product features for candidates
        product_features_list = []
        for pid in candidate_product_ids:
            product_features = self.get_product_features(f"product_{pid}")
            product_features_list.append(product_features)

        product_features_array = np.array(product_features_list)
        product_features_tensor = torch.FloatTensor(product_features_array).to(self.device)

        # Rank candidates using the ranking model
        with torch.no_grad():
            # We need to batch the user features for each candidate
            user_features_batch = user_features_tensor.repeat(len(candidate_product_ids), 1)
            scores = self.ranking_model(user_features_batch, product_features_tensor)
            scores = scores.cpu().numpy().flatten()

        # Get top-k
        top_k_indices = np.argsort(scores)[::-1][:k]
        top_k_product_ids = [candidate_product_ids[i] for i in top_k_indices]
        top_k_scores = [scores[i] for i in top_k_indices]

        # Apply filtering
        filtered_recommendations = self.filter.filter(
            user_id=user_id,
            recommendations=list(zip(top_k_product_ids, top_k_scores))
        )

        return filtered_recommendations