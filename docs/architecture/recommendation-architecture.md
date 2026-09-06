# Recommendation Architecture

## Two-Stage Architecture

The recommendation system uses a two-stage approach to balance accuracy and latency:

### Stage 1: Candidate Generation

The goal of candidate generation is to quickly produce a set of relevant items (candidates) from the entire catalog. This stage prioritizes recall over precision.

#### Embedding-Based Candidate Generator

- Uses learned embeddings for users and items.
- Computes similarity between the user embedding and all item embeddings.
- Returns the top-N most similar items as candidates.
- Implemented using approximate nearest neighbor search (ANN) for scalability (not implemented in this version).

#### Popularity-Based Candidate Generator

- Recommends items based on their overall popularity.
- Popularity is computed as a weighted sum of views, clicks, and purchases.
- Serves as a fallback and helps with cold-start problems.

### Stage 2: Ranking

The goal of ranking is to score the candidates generated in stage 1 and order them by predicted relevance. This stage prioritizes precision.

#### Ranking Model

- Takes user features and item features as input.
- Outputs a score representing the likelihood of user engagement (e.g., click, purchase).
- Implemented as a neural network (or gradient boosted decision tree).
- Trained on historical interaction data.

## Pipeline

1. **User Feature Retrieval** - Fetch user features from the feature store.
2. **Candidate Generation** - Generate 100-500 candidates using embedding-based and/or popularity-based methods.
3. **Feature Retrieval for Candidates** - Fetch features for each candidate product.
4. **Scoring** - Use the ranking model to score each candidate.
5. **Sorting** - Sort candidates by score in descending order.
6. **Filtering** - Remove unavailable items, duplicates, and apply business rules.
7. **Top-K Selection** - Return the top-K recommendations.

## Handling Cold Start

- **New Users**: Use popularity-based candidate generation or default to popular items.
- **New Items**: Use content-based features or rely on popularity until sufficient interaction data is collected.
- **Sparse Users**: Use embedding-based candidate generation with regularization to avoid overfitting to popular items.

## Evaluation

- **Online Metrics**: Click-through rate (CTR), conversion rate, revenue per user.
- **Offline Metrics**: Precision@K, recall@K, mean average precision (MAP), normalized discounted cumulative gain (NDCG).
- **A/B Testing**: Used to compare different recommendation strategies in production.