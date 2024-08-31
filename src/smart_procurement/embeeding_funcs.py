from smart_procurement.embeeders import MixedbreadEmbedder
from chromadb import Documents, EmbeddingFunction, Embeddings


class MixedbreadEmbeddingFunction(EmbeddingFunction):
    def __init__(self, embedder: MixedbreadEmbedder):
        self.embedder = embedder

    def __call__(self, input: Documents) -> Embeddings:
        embeddings = self.embedder.generate_embeddings(input)
        return [embedding.tolist() for embedding in embeddings]
