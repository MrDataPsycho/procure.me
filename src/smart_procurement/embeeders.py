from typing import List
import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class MixedbreadEmbedder:
    def __init__(
        self, model_name="mixedbread-ai/mxbai-embed-large-v1", truncate_dim=1024
    ):
        self.dimensions = truncate_dim
        self.model = SentenceTransformer(model_name, truncate_dim=truncate_dim)
        logger.info(f"Model loaded from {model_name}")

    def generate_embeddings(self, docs: List[str]) -> List[List[float]]:
        if not isinstance(docs, list):
            raise TypeError("Input must be a list of sentences.")

        if not all(isinstance(sentence, str) for sentence in docs):
            raise TypeError("All elements in the input list must be strings.")

        logger.info(
            f"Generating embeddings for {len(docs)} sentences with {self.dimensions} dimensions."
        )
        embeddings = self.model.encode(docs)
        return embeddings

    def __len__(self):
        return self.dimensions

    def __str__(self):
        return f"MixedbreadEmbedder(dimensions={self.dimensions})"

    def __repr__(self):
        return self.__str__()
