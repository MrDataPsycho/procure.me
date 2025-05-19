"""
ETL Pipeline for loading data from JSON files into LanceDB vector store.
"""
import json
import logging
from pathlib import Path
from typing import Union, Dict, Any

from procureme.models.contract_model import ParsedDocument
from procureme.vectordb.lance_vectordb import LanceDBVectorStore
from procureme.clients.ollama_embedder import OllamaEmbeddingClient


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("document_etl")


class DocumentETLPipeline:
    """
    ETL Pipeline for loading documents from JSON files into vector store.
    """
    
    def __init__(
        self,
        vector_store: LanceDBVectorStore,
        batch_size: int = 100,
    ):
        """
        Initialize the ETL pipeline.
        
        Args:
            vector_store: Vector store instance to use for storing documents
            batch_size: Number of documents to process in a batch
        """
        self.vector_store = vector_store
        self.batch_size = batch_size
        logger.info(f"Initialized ETL pipeline with batch size {batch_size}")
    
    def load_from_json_directory(
        self, 
        directory_path: Union[str, Path],
        upsert: bool = False,
    ) -> Dict[str, Any]:
        """
        Load documents from a directory of JSON files.
        
        Args:
            directory_path: Path to directory containing JSON files
            upsert: Whether to upsert documents (update if exists) instead of insert
            
        Returns:
            Dictionary containing stats about the ETL process
        """
        if isinstance(directory_path, str):
            directory_path = Path(directory_path)
        
        if not directory_path.exists() or not directory_path.is_dir():
            raise ValueError(f"Directory {directory_path} does not exist or is not a directory")
        
        # Get all JSON files
        json_files = list(directory_path.glob("*.json"))
        logger.info(f"Found {len(json_files)} JSON files in {directory_path}")
        
        # Track statistics
        stats = {
            "total_files": len(json_files),
            "processed_files": 0,
            "skipped_files": 0,
            "total_documents": 0,
            "errors": [],
        }
        
        # Process files in batches
        current_batch = []
        
        for file_path in json_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    parsed_doc = ParsedDocument.model_validate(data)
                    
                    # Add to current batch
                    current_batch.append(parsed_doc)
                    
                    # Update stats
                    stats["processed_files"] += 1
                    stats["total_documents"] += 1
                    
                    # Process batch if reached batch size
                    if len(current_batch) >= self.batch_size:
                        if upsert:
                            self.vector_store.upsert(current_batch)
                        else:
                            self.vector_store.insert(current_batch)
                        logger.info(f"Processed batch of {len(current_batch)} documents")
                        current_batch = []
                    
            except Exception as e:
                error_msg = f"Error processing {file_path}: {e}"
                logger.error(error_msg)
                stats["errors"].append(error_msg)
                stats["skipped_files"] += 1
        
        # Process any remaining documents
        if current_batch:
            if upsert:
                self.vector_store.upsert(current_batch)
            else:
                self.vector_store.insert(current_batch)
            logger.info(f"Processed final batch of {len(current_batch)} documents")
        
        logger.info(f"ETL process completed. Stats: {stats}")
        return stats


def main():
    """Example usage of the ETL pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Load documents from JSON files into vector store")
    parser.add_argument("--db-path", type=str, required=True, help="Path to LanceDB database")
    parser.add_argument("--table-name", type=str, required=True, help="Name of the table")
    parser.add_argument("--data-dir", type=str, required=True, help="Directory containing JSON files")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for processing")
    parser.add_argument("--upsert", action="store_true", help="Upsert documents instead of insert")
    
    args = parser.parse_args()
    
    # Initialize embedding client
    embedding_client = OllamaEmbeddingClient()
    
    # Initialize vector store
    vector_store = LanceDBVectorStore(
        db_path=args.db_path,
        table_name=args.table_name,
        embedding_client=embedding_client
    )
    
    # Initialize ETL pipeline
    etl = DocumentETLPipeline(vector_store=vector_store, batch_size=args.batch_size)
    
    # Load documents
    stats = etl.load_from_json_directory(args.data_dir, upsert=args.upsert)
    
    print(f"ETL process completed with stats: {stats}")


if __name__ == "__main__":
    main()