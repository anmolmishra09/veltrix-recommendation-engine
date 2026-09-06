"""
Neural ranker using PyTorch.
"""
import torch
import torch.nn as nn
import torch.optim as optim
from .base import BaseRanker
import logging
import numpy as np
import pandas as pd
import os
from typing import List

logger = logging.getLogger(__name__)

class NeuralRanker(nn.Module, BaseRanker):
    def __init__(self, input_dim: int, hidden_dims: List[int] = [128, 64], dropout_rate: float = 0.2):
        """
        Initialize the neural ranker.

        Args:
            input_dim: Number of input features.
            hidden_dims: List of hidden layer sizes.
            dropout_rate: Dropout rate.
        """
        nn.Module.__init__(self)
        BaseRanker.__init__(self)
        self.input_dim = input_dim
        self.hidden_dims = hidden_dims
        self.dropout_rate = dropout_rate

        # Build the network
        layers = []
        prev_dim = input_dim
        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout_rate))
            prev_dim = hidden_dim
        layers.append(nn.Linear(prev_dim, 1))  # Output layer
        self.network = nn.Sequential(*layers)

    def forward(self, x):
        return self.network(x).squeeze(-1)

    def train(self, X: Union[np.ndarray, pd.DataFrame], y: Union[np.ndarray, pd.Series],
              epochs: int = 10, batch_size: int = 256, learning_rate: float = 0.001):
        """
        Train the neural ranker.

        Args:
            X: Feature matrix of shape (n_samples, n_features).
            y: Target vector of shape (n_samples,).
            epochs: Number of training epochs.
            batch_size: Batch size for training.
            learning_rate: Learning rate for optimizer.
        """
        # Convert to numpy arrays
        if isinstance(X, pd.DataFrame):
            if self.feature_names is None:
                self.feature_names = list(X.columns)
            X_array = X.values.astype(np.float32)
        else:
            X_array = X.astype(np.float32)

        if isinstance(y, pd.Series):
            y_array = y.values.astype(np.float32)
        else:
            y_array = y.astype(np.float32)

        # Create PyTorch dataset
        dataset = torch.utils.data.TensorDataset(
            torch.from_numpy(X_array),
            torch.from_numpy(y_array)
        )
        dataloader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)

        # Define loss function and optimizer
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.parameters(), lr=learning_rate)

        # Training loop
        self.train()
        for epoch in range(epochs):
            total_loss = 0
            for batch_X, batch_y in dataloader:
                optimizer.zero_grad()
                outputs = self(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
            avg_loss = total_loss / len(dataloader)
            logger.info(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")

        self.is_trained = True
        logger.info("Neural ranker trained successfully")

    def predict(self, X: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """
        Predict scores using the neural ranker.

        Args:
            X: Feature matrix of shape (n_samples, n_features).

        Returns:
            Predicted scores of shape (n_samples,).
        """
        if not self.is_trained:
            raise Exception("Model has not been trained yet")

        self.eval()
        if isinstance(X, pd.DataFrame):
            X_array = X.values.astype(np.float32)
        else:
            X_array = X.astype(np.float32)

        with torch.no_grad():
            tensor_X = torch.from_numpy(X_array)
            predictions = self(tensor_X).numpy()
        return predictions

    def save(self, path: str):
        """
        Save the neural ranker to a file.

        Args:
            path: Path to save the ranker (without extension).
        """
        if not self.is_trained:
            raise Exception("Model has not been trained yet")

        # Save the model state dict
        model_path = f"{path}.pt"
        torch.save({
            'model_state_dict': self.state_dict(),
            'input_dim': self.input_dim,
            'hidden_dims': self.hidden_dims,
            'dropout_rate': self.dropout_rate,
            'feature_names': self.feature_names
        }, model_path)

        logger.info(f"Neural ranker saved to {model_path}")

    def load(self, path: str):
        """
        Load the neural ranker from a file.

        Args:
            path: Path to the saved ranker (without extension).
        """
        # Load the model state dict
        model_path = f"{path}.pt"
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")

        checkpoint = torch.load(model_path)
        self.input_dim = checkpoint['input_dim']
        self.hidden_dims = checkpoint['hidden_dims']
        self.dropout_rate = checkpoint['dropout_rate']
        self.feature_names = checkpoint['feature_names']

        # Rebuild the network
        layers = []
        prev_dim = self.input_dim
        for hidden_dim in self.hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(self.dropout_rate))
            prev_dim = hidden_dim
        layers.append(nn.Linear(prev_dim, 1))
        self.network = nn.Sequential(*layers)

        # Load the state dict
        self.load_state_dict(checkpoint['model_state_dict'])
        self.is_trained = True
        logger.info(f"Neural ranker loaded from {model_path}")

    def get_feature_importance(self) -> Optional[dict]:
        """
        Get feature importance is not straightforward for neural networks.
        We can return None or use a surrogate method like permutation importance.
        For simplicity, we return None.
        """
        return None