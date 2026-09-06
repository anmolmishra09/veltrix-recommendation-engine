# Candidate Generation

## Overview

Candidate generation is the first stage of the recommendation system, where we quickly identify a set of relevant items from the entire catalog. The goal is to maximize recall (i.e., capture as many relevant items as possible) while keeping the candidate set small enough for the ranking stage to process efficiently.

## Approaches

### 1. Embedding-Based Candidate Generation

#### How It Works
- Learn dense vector representations (embeddings) for users and items such that similar users and items have similar vectors.
- Represent each user and item as a point in a shared embedding space.
- For a given user, compute the similarity between the user's embedding and all item embeddings.
- Return the top-K most similar items as candidates.

#### Similarity Metrics
- **Cosine Similarity**: Measures the cosine of the angle between two vectors. Ranges from -1 to 1, where 1 means identical direction.
- **Dot Product**: Equivalent to cosine similarity when vectors are normalized.
- **Euclidean Distance**: Measures the straight-line distance between two points (smaller means more similar).

#### Implementation
- We use two embedding tables: one for users and one for items.
- The embedding tables are learned implicitly through the ranking model or explicitly through separate training (e.g., using Word2Vec or matrix factorization).
- At inference time, we retrieve the user embedding and compute similarities with all item embeddings.
- To scale to large catalogs, we use approximate nearest neighbor (ANN) search algorithms (e.g., FAISS, Annoy, or ScaNN) to avoid computing similarities with all items.

#### Advantages
- Captures complex, non-linear relationships between users and items.
- Generalizes to new users and items based on their features (if using content-augmented embeddings).
- Efficient at query time with ANN.

#### Disadvantages
- Requires training or learning embeddings, which adds complexity.
- May suffer from popularity bias if not regularized properly.
- Embedding quality depends on the training data and algorithm.

### 2. Popularity-Based Candidate Generation

#### How It Works
- Rank items by their overall popularity (e.g., number of interactions, revenue generated).
- Recommend the top-K most popular items to all users.
- Serve as a strong baseline and help with cold-start scenarios.

#### Popularity Metrics
- **Total Interactions**: Sum of views, clicks, and purchases.
- **Weighted Interactions**: Assign different weights to different interaction types (e.g., a purchase is worth more than a click).
- **Time-Decayed Interactions**: Give more weight to recent interactions to capture changing trends.

#### Implementation
- Precompute popularity scores for all items periodically (e.g., hourly or daily).
- Store the scores in a lookup table or database.
- At request time, retrieve the top-K items from the precomputed list.

#### Advantages
- Simple to implement and understand.
- Very fast at query time (just a lookup).
- Effective for new users (cold start) and for increasing overall platform engagement.

#### Disadvantages
- Not personalized; everyone gets the same recommendations.
- Can lead to a rich-get-richer effect, where popular items become even more popular.
- Does not capture niche interests.

### 3. Hybrid Candidate Generation

#### How It Works
- Combine multiple candidate generation approaches to leverage their strengths.
- Common strategies:
  - **Union**: Take the union of candidates from multiple methods.
  - **Intersection**: Take the intersection (more conservative).
  - **Weighted Combination**: Score candidates using a weighted sum of scores from different methods.
  - **Cascading**: Use one method to generate candidates, then filter or re-rank using another.

#### Implementation in This Platform
- We implement both embedding-based and popularity-based candidate generators.
- The recommender can switch between them or use both (not implemented in this version).
- A simple hybrid approach would be to take the top-N from each method and combine them.

## Cold Start Handling

### New Users
- **Problem**: No interaction history for the user.
- **Solutions**:
  1. Use popularity-based candidate generation.
  2. Use demographic or content-based features if available (not implemented).
  3. Assign a random or default embedding and update it as interactions occur.

### New Items
- **Problem**: No interaction history for the item.
- **Solutions**:
  1. Use content-based features to generate an embedding for the item (not implemented).
  2. Give the item a small initial popularity score to allow it to be recommended.
  3. Use exploration strategies (e.g., epsilon-greedy) to recommend new items occasionally.

## Evaluation

### Online Metrics
- **Recall@K**: Percentage of actual interactions that appear in the top-K candidates.
- **Mean Reciprocal Rank (MRR)**: Average of the reciprocal ranks of the first relevant item.
- **Coverage**: Percentage of the item catalog that is recommended over a period.

### Offline Metrics (if ground truth is available)
- **Hit Rate@K**: Percentage of users for whom at least one actual interaction is in the top-K candidates.
- **Average Number of Candidates**: Average size of the candidate set per user.

## Implementation Notes

### Embedding Tables
- The embedding tables are stored as part of the ranking model or as separate models.
- In this implementation, the embedding model is a PyTorch model with two embedding layers (one for users, one for items).

### Similarity Computation
- For small to medium catalogs (<100k items), we compute similarities exhaustively.
- For large catalogs, we integrate with an ANN library (e.g., FAISS) to speed up search.

### Precomputation
- Item embeddings are precomputed and stored in memory to avoid recomputing them for every request.
- User embeddings are computed on the fly since they are specific to the request.

## Configuration

- **Number of Candidates**: Controls how many candidates are passed to the ranking stage (default: 100).
- **Similarity Metric**: Choice of cosine similarity, dot product, or Euclidean distance (default: cosine similarity).
- **ANN Library**: If enabled, specifies the ANN library and its parameters (e.g., number of trees for Annoy).

## Example Usage

```python
from ml.recommendation.candidate_generation.embedding_based import EmbeddingBasedCandidateGenerator
from ml.embeddings.user_embeddings import UserEmbedding
from ml.embeddings.product_embeddings import ProductEmbedding

# Initialize embeddings (learned from training)
user_embedding = UserEmbedding()
user_embedding.load("./models/user_embeddings.npy")

product_embedding = ProductEmbedding()
product_embedding.load("./models/product_embeddings.npy")

# Initialize candidate generator
candidate_generator = EmbeddingBasedCandidateGenerator(
    user_embedding=user_embedding,
    product_embedding=product_embedding
)

# Generate candidates for a user
candidates = candidate_generator.generate(
    user_id="user_123",
    limit=100
)
```