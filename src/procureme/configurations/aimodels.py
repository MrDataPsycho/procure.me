from enum import StrEnum

class ChatModelSelection(StrEnum):
    GEMMA3 = "gemma3:4b"
    GPT3 = "gpt-3.5-turbo-0125"
    GPT4_1_NANO = "gpt-4.1-nano"
    GPT4_1_MINI = "gpt-4.1-mini-2025-04-14"
    LLAMA31 = "llama3.1:latest"


class EmbeddingModelSelection(StrEnum):
    EMBED_SMALL = "text-embedding-3-small"
    EMBED_LARGE = "text-embedding-3-large"
    EMBED_ADA = "text-embedding-ada-002"
    NOMIC = "nomic-embed-text:v1.5"

