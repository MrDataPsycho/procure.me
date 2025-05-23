from abc import ABC, abstractmethod
from typing import List


class EmbeddingClientABC(ABC):
    """Abstract base class for embedding clients."""
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the dimension of the embeddings produced by this client."""
        pass
    
    @abstractmethod
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for a query text."""
        pass
    
    @abstractmethod
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts in batch."""
        pass