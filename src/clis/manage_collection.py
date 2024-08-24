import chromadb.errors
import typer
import asyncio
import chromadb
from dotenv import load_dotenv
import os
from smart_procurement.embeeders import MixedbreadEmbedder
from smart_procurement.embeeding_funcs import MixedbreadEmbeddingFunction


app = typer.Typer()
load_dotenv(".envs/dev.env", override=True)
EMB_MODEL_PATH = "models/embeddings/mxbai-embed-large-v1"
CLIENT = chromadb.HttpClient(host=os.environ["CHROMA_DB_HOST"], port=os.environ["CACHING_DB_PORT"])



# Function to create an async ChromaDB client

@app.command()
def delete_collection(
    collection_name: str, 
    empty: bool = typer.Option(False, "--empty", help="Empty the collection instead of deleting it")):
    """
    Delete a ChromaDB collection or empty its contents.
    
    Arguments:
    collection_name: The name of the collection to delete or empty.
    empty: If set to True, empties the collection instead of deleting it.
    """
    collection = None
    
    # Try to get the collection
    try:
        collection = CLIENT.get_collection(collection_name)
    except chromadb.errors.InvalidCollectionException as e:
        typer.echo(f"Collection '{collection_name}' does not exist. {e}")
        return
    
    if empty:
        # Empty the collection
        collection.delete()
        typer.echo(f"Collection '{collection_name}' emptied successfully.")
    else:
        # Delete the entire collection
        CLIENT.delete_collection(collection_name)
        typer.echo(f"Collection '{collection_name}' deleted successfully.")


@app.command()
def create_collection(collection_name: str):
    """
    Create a new collection in the ChromaDB server.
    
    Arguments:
    collection_name: The name of the collection to create.
    """
    try:
        collection = CLIENT.get_or_create_collection(
            collection_name,
            embedding_function=MixedbreadEmbeddingFunction(
                embedder=MixedbreadEmbedder(EMB_MODEL_PATH)
            ),
            metadata={
                "hnsw:space": "cosine",
                "hnsw:construction_ef": 100,
            }
        )
        typer.echo(f"Collection '{collection_name}' created or retrieved successfully. {collection}")
    except Exception as e:
        typer.echo(f"Error creating collection '{collection_name}': {e}")

if __name__ == "__main__":
    # Examples
    # python src/clis/manage_collection.py create-collection collection_name
    # python src/clis/manage_collection.py delete-collection collection_name
    # python src/clis/manage_collection.py delete-collection collection_name --empty
    asyncio.run(app())
