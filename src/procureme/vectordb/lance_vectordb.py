import lancedb
from lancedb.pydantic import Vector, LanceModel
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from procureme.clients.embedder import EmbeddingClientABC
from procureme.vectordb.interface import VectorDBABC
from procureme.models.contract_model import ParsedDocument
import json
 

DEFAULT_DIMENSION = 768

def get_schema_by_dimension(dimension: int) -> type[LanceModel]:
    class DocumentWithMetadata(LanceModel):
        """Lance DB model for document chunks with metadata."""
        chunk_id: str
        doc_id: str
        file_name: str
        total_pages: int
        content: str
        part: str
        vector: Vector(dimension)
    return DocumentWithMetadata


class LanceDBVectorStore(VectorDBABC):
    """LanceDB implementation of VectorDBABC interface."""
    
    def __init__(
        self, 
        db_path: Union[str, Path], 
        table_name: str,
        embedding_client: Optional[EmbeddingClientABC] = None,
    ):
        """
        Initialize the LanceDB vector store.
        
        Args:
            db_path: Path to the LanceDB database file
            table_name: Name of the table to use
            embedding_client: Optional pre-configured embedding client
        """
        self.db_path = Path(db_path) if isinstance(db_path, str) else db_path
        self.table_name = table_name
        self.embedding_client = embedding_client
        self._dimension = self.embedding_client.dimension
        self.db = None
        self.table = None
        self.connect()
    
    @property
    def dimension(self) -> int:
        """Get the dimension of the vectors used in the database."""
        return self._dimension
    
    def connect(self) -> None:
        """Connect to the LanceDB database and open or create the table."""
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Connect to the database
        self.db = lancedb.connect(self.db_path)
        
        # Open existing table or create new one
        if self.table_name in self.db.table_names():
            self.table = self.db.open_table(self.table_name)
        
        else:
            self.table = self.db.create_table(
                self.table_name, 
                schema=get_schema_by_dimension(self.dimension)
            )
    
    def save(self) -> None:
        """Save the database. 
        
        For LanceDB, this is a no-op as changes are saved automatically.
        """
        # LanceDB saves automatically, so this is a no-op
        pass
    
    def load(self) -> None:
        """Load the database.
        
        For LanceDB, this reconnects to the database.
        """
        self.connect()
    
    def search(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        """
        Search for the top_k most similar documents to the query.
        
        Args:
            query: The query text to search for
            top_k: The number of results to return
            
        Returns:
            List of document dictionaries with similarity scores
        """
        if self.table is None:
            self.connect()
        
        # Generate embedding for the query using the embedding client
        query_vector = self.embedding_client.get_embedding(query)
        selected_columns = ['chunk_id', 'doc_id', 'file_name', 'total_pages', 'content', 'part', '_distance']
        # Perform vector search
        results = self.table.search(query_vector).limit(top_k).select(selected_columns).to_list()
        
        # Convert to list of dictionaries
        return results
    
    def insert(self, documents: List[Union[ParsedDocument, Dict]]) -> None:
        """
        Insert documents into the database.
        
        Args:
            documents: List of ParsedDocument objects or dictionaries
        """
        if self.table is None:
            self.connect()
        
        lance_documents = []
        for doc in documents:
            if isinstance(doc, dict):
                doc = ParsedDocument.model_validate(doc)
            
            lance_docs = self._convert_doc_to_lance_format(doc)
            lance_documents.extend(lance_docs)
        
        if lance_documents:
            self.table.add(lance_documents)
    
    def delete(self, index_id: str) -> None:
        """
        Delete documents from the database.
        
        Args:
            index_id: The ID of the document chunk to delete
        """
        if self.table is None:
            self.connect()
        
        # For LanceDB, we use a where clause to delete by chunk_id
        self.table.delete(f'chunk_id = "{index_id}"')
    
    def upsert(self, documents: List[Union[ParsedDocument, Dict]]) -> None:
        """
        Upsert documents into the database (insert if not exists, update if exists).
        
        Args:
            documents: List of ParsedDocument objects or dictionaries
        """
        if self.table is None:
            self.connect()
        
        lance_documents = []
        for doc in documents:
            if isinstance(doc, dict):
                doc = ParsedDocument.model_validate(doc)
            
            lance_docs = self._convert_doc_to_lance_format(doc)
            lance_documents.extend(lance_docs)
        
        if lance_documents:
            # Use merge_insert for upsert operation
            self.table.merge_insert("chunk_id") \
                .when_matched_update() \
                .when_not_matched_insert_all() \
                .execute(lance_documents)


    def _convert_doc_to_lance_format(self, doc: ParsedDocument) -> List[LanceModel]:
        """
        Convert a ParsedDocument to LanceDB format.
        
        Args:
            doc: ParsedDocument object
            
        Returns:
            List of DocumentWithMetadata objects
        """
        documents = []
        for part in doc.parts:
            # Generate embedding for the text using the embedding client
            vector = self.embedding_client.get_embedding(part.text)
            schema = get_schema_by_dimension(self.dimension)
            document_unit = schema(
                chunk_id=f"{doc.file_name}-{part.part}",
                doc_id=doc.id_,
                file_name=doc.file_name,
                total_pages=doc.total_pages,
                content=part.text,
                part=part.part,
                vector=vector,
            )
            documents.append(document_unit)
        return documents

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector database.
        
        Returns:
            Dictionary containing stats about the database
        """
        if self.table is None:
            self.connect()
            
        stats = {
            "total_documents": len(self.table),
            "dimension": self.dimension,
            "db_path": str(self.db_path),
            "table_name": self.table_name,
            "embedding_model": str(self.embedding_client)
        }
        return stats

    def load_from_json_directory(self, directory_path: Union[str, Path]) -> None:
        """
        Load documents from a directory of JSON files.
        
        Args:
            directory_path: Path to directory containing JSON files
        """
        if isinstance(directory_path, str):
            directory_path = Path(directory_path)
        
        if not directory_path.exists() or not directory_path.is_dir():
            raise ValueError(f"Directory {directory_path} does not exist or is not a directory")
        
        # Get all JSON files
        json_files = list(directory_path.glob("*.json"))
        
        documents = []
        for file_path in json_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    parsed_doc = ParsedDocument.model_validate(data)
                    documents.append(parsed_doc)
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
        
        # Insert all documents
        if documents:
            self.insert(documents)


if __name__ == "__main__":
    from procureme.clients.ollama_embedder import OllamaEmbeddingClient
    CLIENT = OllamaEmbeddingClient()
    DBPATH = Path("vectordb").joinpath("contracts.db")
    TABLE_NAME = "contracts_naive"
    vector_store = LanceDBVectorStore(db_path=DBPATH, table_name=TABLE_NAME, embedding_client=CLIENT)
    print(vector_store.get_stats())