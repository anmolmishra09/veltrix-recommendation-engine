# Ranking

## Overview

Ranking is the second stage of the recommendation system, where we score the candidates generated in the first stage to determine their relevance to the user. The goal is to maximize precision (i.e., ensure that the top-ranked items are truly relevant) while maintaining a good user experience.

## Approaches

### 1. Pointwise Ranking

#### How It Works
- Treat each user-item pair as an independent example.
- Predict a score or probability that represents the likelihood of a specific interaction (e.g., click, purchase).
- Common loss functions: logistic regression (for binary outcomes), linear regression (for ratings), or Poisson regression (for counts).

#### Advantages
- Simple to implement and understand.
- Can use well-established algorithms (e.g., logistic regression, decision trees, neural networks).
- Outputs are interpretable as probabilities or expected values.

#### Disadvantages
- Ignores the positional nature of rankings (i.e., the fact that we care about the order of items).
- May not optimize directly for ranking metrics like NDCG or MAP.

### 2. Pairwise Ranking

#### How It Works
- Treat pairs of items (i, j) as examples, where the goal is to predict whether item i is preferred over item j.
- Learn a ranking function that minimizes the number of misordered pairs.
- Common algorithms: RankNet, RankBoost, LambdaRank.

#### Advantages
- Directly optimizes for ordering preferences.
- Can capture complex relationships between items.

#### Disadvantages
- Computationally more expensive than pointwise (number of pairs grows quadratically with the number of items).
- The output scores are not as easily interpretable as probabilities.

### 3. Listwise Ranking

#### How It Works
- Treat the entire list of items as an example.
- Optimize a ranking metric directly (e.g., NDCG, MAP, or MRR).
- Common algorithms: LambdaMART, ListNet, ListMLE.

#### Advantages
- Directly optimizes for the desired ranking metric.
- Can capture complex interactions and dependencies between items in a list.

#### Disadvantations
- Most complex to implement and train.
- Requires the entire list of items for each user, which can be memory-intensive.

## Implementation in This Platform

We use a pointwise approach for simplicity and efficiency. The ranking model predicts the probability that a user will interact with a given item (e.g., click or purchase) based on user features, item features, and contextual features.

### Model Architecture
- **Input**: Concatenation of user features and item features.
- **Hidden Layers**: One or more fully connected layers with ReLU activation.
- **Output**: A single sigmoid unit outputting a probability between 0 and 1.

### Features Used
#### User Features
- Historical interaction counts (views, clicks, purchases).
- Historical spending.
- Time since last interaction.
- User demographics (if available).
- User embedding (if using content-augmented models).

#### Item Features
- Historical interaction counts (views, clicks, purchases).
- Item attributes (category, price, brand, etc.).
- Item embedding (if using content-augmented models).
- Inventory status (if available).

#### Contextual Features
- Time of day.
- Day of week.
- Device type.
- Referrer source.

### Training
- **Loss Function**: Binary cross-entropy (for predicting click/no-click or purchase/no-purchase).
- **Optimizer**: Adam or SGD with momentum.
- **Batch Size**: Typically 256-1024.
- **Epochs**: Trained until convergence on a validation set.
- **Regularization**: Dropout, weight decay (L2 regularization) to prevent overfitting.

### Serving
- The model is loaded into memory and serves predictions in real-time.
- Input features are retrieved from the feature store and concatenated.
- The model runs a forward pass to produce a score.
- Scores are used to sort candidates in descending order.

## Advantages of Pointwise Ranking in This Context

- **Simplicity**: Easier to implement, debug, and maintain.
- **Efficiency**: Fast inference time, especially when batching multiple items for the same user.
- **Flexibility**: Can easily incorporate new features by adjusting the input size.
- **Interpretability**: Output probabilities can be calibrated and used for business decisions.

## Disadvantages and Mitigations

### Does Not Optimize for Ranking Metrics Directly
- **Mitigation**: We can use listwise or pairwise approaches in future iterations if ranking metrics are not satisfactory.
- **Alternative**: We can calibrate the scores to better reflect ranking performance.

### Feature Interaction Limitations
- **Mitigation**: Use deeper networks or specialized architectures (e.g., Factorization Machines) to capture feature interactions.
- **Alternative**: Manually engineer interaction features (e.g., user_category * item_category).

## Evaluation

### Online Metrics
- **Click-Through Rate (CTR)**: Percentage of recommended items that are clicked.
- **Conversion Rate**: Percentage of recommended items that lead to a purchase.
- **Revenue per Recommendation (RPR)**: Average revenue generated from a recommended item.
- **Ranking Metrics**: Precision@K, Recall@K, NDCG@K (computed from live experiment data).

### Offline Metrics (if ground truth is available)
- **Area Under the ROC Curve (AUC)**: Measures the model's ability to distinguish between positive and negative examples.
- **Log Loss**: Measures the uncertainty of the model's predictions.
- **Mean Squared Error (MSE)**: For regression settings (e.g., predicting ratings).
- **Precision@K, Recall@K, NDCG@K**: Computed on a held-out test set.

## Implementation Details

### Model Definition (ml/recommendation/ranking/model.py)
```python
import torch
import torch.nn as nn

class RankingModel(nn.Module):
    def __init__(self, user_feature_dim, product_feature_dim, hidden_dim=128):
        super(RankingModel, self).__init__()
        self.fc1 = nn.Linear(user_feature_dim + product_feature_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, 1)
        self.relu = nn.ReLU()
        self.sigmoid = nn.Sigmoid()
        self.dropout = nn.Dropout(0.2)

    def forward(self, user_features, product_features):
        # Concatenate user and product features
        x = torch.cat([user_features, product_features], dim=1)
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.relu(self.fc2(x))
        x = self.dropout(x)
        x = self.fc3(x)
        return self.sigmoid(x)
```

### Model Training (ml/train.py)
- Loads training data from the feature store (offline store).
- Splits data into training and validation sets.
- Trains the model using PyTorch.
- Logs the model to MLflow with metadata (e.g., training date, feature version).

### Model Serving (apps/api/recommender.py)
- Uses the model loader to get the latest ranking model.
- Retrieves user features from the feature store.
- Retrieves product features for each candidate from the feature store.
- Concatenates features and passes them to the model.
- Applies the sigmoid activation to get a probability.

## Performance Considerations

### Latency
- **Feature Retrieval**: Dominated by the feature store lookup (typically 1-5ms per feature vector).
- **Model Inference**: Depends on model size and hardware (typically 1-10ms for a batch of 100 items on CPU).
- **Batching**: We batch the user features for all candidates to improve inference efficiency.

### Throughput
- **Horizontal Scaling**: Multiple instances of the API service can be deployed behind a load balancer.
- **Model Server**: In the future, we could extract the model serving into a separate service (e.g., using TorchServe or TensorFlow Serving) to allow independent scaling.

## Security

- **Input Validation**: User and product IDs are validated to prevent injection attacks.
- **Model Integrity**: Models are loaded from trusted sources (MLflow or signed local files).
- **No Arbitrary Code Execution**: The model loader does not execute code from the model file; it only loads the model weights.

## Future Improvements

### 1. Implement Pairwise or Listwise Approaches
- To better optimize for ranking metrics like NDCG and MAP.

### 2. Use Feature Interaction Layers
- Such as Factorization Machines or Neural Factorization Machines to explicitly model feature interactions.

### 3. Implement Model Quantization
- To reduce model size and improve inference speed on CPU.

### 4. Add Multi-Task Learning
- To predict multiple engagement types (e.g., click, like, share, purchase) simultaneously.

### 5. Implement Contextual Bandits
- For exploration-exploitation trade-offs in recommendation lists.

## Configuration

- **Hidden Layer Sizes**: Comma-separated list of hidden layer sizes (default: "128").
- **Dropout Rate**: Fraction of neurons to drop during training (default: 0.2).
- **Learning Rate**: Initial learning rate for the optimizer (default: 0.001).
- **Batch Size**: Number of samples per training batch (default: 256).
- **Epochs**: Number of training epochs (default: 10).
- **Validation Split**: Fraction of training data to use for validation (default: 0.2).