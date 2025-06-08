from procureme.clients.embedder import EmbeddingClientABC
from typing import List
from openai import OpenAI
import os
from procureme.configurations.aimodels import EmbeddingModelSelection


class OpenAIEmbeddingClient(EmbeddingClientABC):
    """Ollama implementation of the EmbeddingClientABC interface."""
    
    def __init__(
        self,
        model_name: str = "text-embedding-3-small",
    ):
        """
        Initialize the Ollama embedding client.
        
        Args:
            model_name: Name of the embedding model to use (default: text-embedding-3-small)
        """
        self.model_name = model_name
        
        # Initialize the underlying client
        self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Calculate dimension with a test query
        self._dimension = self._set_embedding_dimension()
    
    def _set_embedding_dimension(self):
        response = self._client.embeddings.create(input="Test embedding dimension", model=self.model_name)
        return len(response.data[0].embedding)
    
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
        response = self._client.embeddings.create(input=text, model=self.model_name)
        return response.data[0].embedding

    
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
        return f"OpenAIEmbeddingClient(model_name={self.model_name}, dimension={self.dimension})"
    

if __name__ == "__main__":
    from dotenv import load_dotenv
    _ = load_dotenv(override=True)

    client = OpenAIEmbeddingClient()
    print(client.dimension)
    query = "I want to buy a keyboard and mouse."
    embedding = client.get_embedding(query)
    print(embedding)