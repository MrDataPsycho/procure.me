import typer
import asyncio
import polars as pl
import chromadb
from typing import List
from dataclasses import dataclass, asdict
from smart_procurement.embeeders import MixedbreadEmbedder
from smart_procurement.embeeding_funcs import MixedbreadEmbeddingFunction
from pathlib import Path
from smart_procurement.models.chroma_cc_model import CommodityCodesListChromaDB

app = typer.Typer()

# Configuration
EMB_MODEL_PATH = "../models/embeddings/mxbai-embed-large-v1"
DATA_PATH = Path().absolute().parent.joinpath("data")
COMMODITY_CODE_FILE_PATH = DATA_PATH.joinpath("raw", "commodity_codes.csv")

# Embedder model
emb_model = MixedbreadEmbedder(EMB_MODEL_PATH)




async def get_chroma_client():
    return await chromadb.AsyncHttpClient(host="localhost", port=8010)


@app.command()
async def create_collection():
    """Create a new collection in the ChromaDB server."""
    client = await get_chroma_client()
    collection = await client.get_or_create_collection(
        "commodity_codes",
        embedding_function=MixedbreadEmbeddingFunction(
            embedder=emb_model
        ),
        metadata={
            "hnsw:space": "cosine",
            "hnsw:construction_ef": 100,
        }
    )
    typer.echo("Collection 'commodity_codes' created successfully.")
    await client.close()


@app.command()
async def delete_collection():
    """Delete the 'commodity_codes' collection from the ChromaDB server."""
    client = await get_chroma_client()
    await client.delete_collection("commodity_codes")
    typer.echo("Collection 'commodity_codes' deleted successfully.")
    await client.close()


@app.command()
async def insert_documents(csv_file: str = typer.Argument(COMMODITY_CODE_FILE_PATH)):
    """Insert documents from a CSV file into the ChromaDB collection."""
    client = await get_chroma_client()
    collection = await client.get_or_create_collection(
        "commodity_codes",
        embedding_function=MixedbreadEmbeddingFunction(
            embedder=emb_model
        ),
    )
    
    # Load the data from the CSV file
    cc_df = pl.read_csv(csv_file, separator="|")
    
    # Convert to the data structure expected by ChromaDB
    test_cc_list = CommodityCodesListChromaDB.from_dict(cc_df.to_dicts())
    cc_documents = test_cc_list.get_chroma_input_document()
    
    # Add documents to the collection
    await collection.add(**cc_documents)
    typer.echo("Documents inserted successfully.")
    await client.close()


if __name__ == "__main__":
    asyncio.run(app())
