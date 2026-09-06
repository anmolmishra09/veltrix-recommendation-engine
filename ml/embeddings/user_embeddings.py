"""
User embeddings.
"""
import pandas as pd
import numpy as np
import os
from .base import BaseEmbedding
import logging
from typing import Union, List

logger = logging.getLogger(__name__)

class UserEmbedding(BaseEmbedding):
    def __init__(self, embedding_dim: int = None):
        super().__init__()
        self.embedding_dim = embedding_dim

    def load(self, path: str, format: str = 'csv'):
        """
        Load user embeddings.

        Supported formats:
        - csv: CSV file with columns 'user_id' and 'embedding_0', 'embedding_1', ..., 'embedding_{n-1}'
        - numpy: .npy file containing a matrix and a separate .npy file for IDs
        - json: JSON file with user_id as key and list of floats as value

        Args:
            path: Path to the embeddings file.
            format: Format of the embeddings file.
        """
        if format == 'csv':
            self._load_from_csv(path)
        elif format == 'numpy':
            self._load_from_numpy(path)
        elif format == 'json':
            self._load_from_json(path)
        else:
            raise ValueError(f"Unsupported format: {format}")

        logger.info(f"Loaded user embeddings for {len(self.id_to_index)} users with dimension {self.embedding_dim}")

    def _load_from_csv(self, path: str):
        df = pd.read_csv(path)
        # Assume first column is user_id
        id_column = df.columns[0]
        embedding_columns = [col for col in df.columns if col.startswith('embedding_')]
        if not embedding_columns:
            # Try to find columns that are numeric and not the id column
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if id_column in numeric_cols:
                numeric_cols.remove(id_column)
            embedding_columns = numeric_cols

        if self.embedding_dim is None:
            self.embedding_dim = len(embedding_columns)
        elif self.embedding_dim != len(embedding_columns):
            raise ValueError(f"Embedding dimension mismatch: expected {self.embedding_dim}, got {len(embedding_columns)}")

        # Sort embedding columns to ensure order
        embedding_columns.sort(key=lambda x: int(x.split('_')[1]) if '_' in x else 0)

        self._embeddings = df[embedding_columns].values.astype(np.float32)
        self.id_to_index = {str(id_val): idx for idx, id_val in enumerate(df[id_column])}
        self.index_to_id = {idx: str(id_val) for idx, id_val in enumerate(df[id_column])}

    def _load_from_numpy(self, path: str):
        embeddings_path = path + '.npy'
        ids_path = path + '_ids.npy'
        if not os.path.exists(embeddings_path) or not os.path.exists(ids_path):
            raise FileNotFoundError(f"Numpy embedding files not found: {embeddings_path} or {ids_path}")

        self._embeddings = np.load(embeddings_path).astype(np.float32)
        ids = np.load(ids_path)
        self.id_to_index = {str(id_val): idx for idx, id_val in enumerate(ids)}
        self.index_to_id = {idx: str(id_val) for idx, id_val in enumerate(ids)}
        self.embedding_dim = self._embeddings.shape[1]

    def _load_from_json(self, path: str):
        import json
        with open(path, 'r') as f:
            data = json.load(f)

        ids = list(data.keys())
        embeddings = list(data.values())

        lengths = [len(vec) for vec in embeddings]
        if len(set(lengths)) != 1:
            raise ValueError("All embeddings must have the same length")

        self.embedding_dim = lengths[0]
        self._embeddings = np.array(embeddings, dtype=np.float32)
        self.id_to_index = {id_val: idx for idx, id_val in enumerate(ids)}
        self.index_to_id = {idx: id_val for idx, id_val in enumerate(ids)}

    def get_embedding(self, id: Union[str, int]) -> np.ndarray:
        id_str = str(id)
        if id_str not in self.id_to_index:
            logger.warning(f"ID {id_str} not found in embeddings. Returning zero vector.")
            return np.zeros(self.embedding_dim, dtype=np.float32)
        idx = self.id_to_index[id_str]
        return self._embeddings[idx]

    def get_embeddings(self, ids: List[Union[str, int]]) -> np.ndarray:
        id_strs = [str(id) for id in ids]
        embeddings = []
        for id_str in id_strs:
            if id_str in self.id_to_index:
                idx = self.id_to_index[id_str]
                embeddings.append(self._embeddings[idx])
            else:
                logger.warning(f"ID {id_str} not found in embeddings. Using zero vector.")
                embeddings.append(np.zeros(self.embedding_dim, dtype=np.float32))
        return np.array(embeddings, dtype=np.float32)