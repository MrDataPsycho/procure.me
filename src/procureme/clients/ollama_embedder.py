from procureme.clients.embedder import EmbeddingClientABC
from typing import Any, Dict, List, Optional
from llama_index.embeddings.ollama import OllamaEmbedding
import os

class OllamaEmbeddingClient(EmbeddingClientABC):
    """Ollama implementation of the EmbeddingClientABC interface."""
    
    def __init__(
        self,
        model_name: str = "nomic-embed-text:v1.5",
        base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        additional_kwargs: Optional[Dict[str, Any]] = None,
        timeout: int = 60
    ):
        """
        Initialize the Ollama embedding client.
        
        Args:
            model_name: Name of the embedding model to use (default: nomic-embed-text:v1.5)
            base_url: Base URL for the Ollama API (default: http://localhost:11434)
            additional_kwargs: Additional keyword arguments to pass to Ollama
            timeout: Timeout for API requests in seconds
        """
        self.model_name = model_name
        self.base_url = base_url
        self.additional_kwargs = additional_kwargs or {"mirostat": 0}
        self.timeout = timeout
        
        # Initialize the underlying client
        self._client = OllamaEmbedding(
            model_name=self.model_name,
            base_url=self.base_url,
            ollama_additional_kwargs=self.additional_kwargs,
            timeout=self.timeout
        )
        
        # Calculate dimension with a test query
        self._dimension = len(self._client.get_query_embedding("Test embedding dimension"))
    
    @property
    def dimension(self) -> int:
        """Return the dimension of the embeddings produced by this client."""
        return self._dimension
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for a query text.
        
        Args:
            text: The text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        embedding = self._client.get_query_embedding(text)
        return embedding

    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for multiple texts in batch.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        for text in texts:
            embedding = self.get_text_embedding(text)
            embeddings.append(embedding)
        return embeddings
    
    def __repr__(self) -> str:
        """Return string representation of the client."""
        return f"OllamaEmbeddingClient(model_name={self.model_name}, dimension={self.dimension})"
    

if __name__ == "__main__":
    client = OllamaEmbeddingClient()
    print(client.dimension)
    query = "I want to buy a keyboard and mouse."
    embedding = client.get_embedding(query)
    print(embedding)