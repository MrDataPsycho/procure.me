"""
FastAPI server for chat interactions with RAG capabilities using LanceDB and Ollama.
"""
import logging
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

# Import Ollama from llama_index as requested
from llama_index.llms.ollama import Ollama
from llama_index.core.llms import ChatMessage, MessageRole

# import ollama
from procureme.clients.ollama_embedder import OllamaEmbeddingClient
from procureme.vectordb.lance_vectordb import LanceDBVectorStore
import re


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("RAGAGent")


# System prompt for RAG
SYSTEM_PROMPT = """
You are a helpful and informative assistant powered by a Retrieval-Augmented Generation (RAG) 
system. Your primary goal is to answer user questions accurately and concisely, leveraging a 
provided context document. You will output your responses in JSON format.

**Instructions:**

1.  **Receive Context:** You will be provided with one or many document as [CONTEXT].
Each start with Header: --- [CONTEXT_DOCUMENT_NAME]: <placeholder document name to fill> [CONTEXT_DOCUMENT_NAME_PARTITION_NUMBER]: <placeholder partition number of the document> ---
Then followed by [CONTENT] of the document containing relevant information. *Carefully read and understand the documents.*

2.  **Receive Query:** You will also receive a user's question (referred to as 
"[USER_QUERY]").

3.  **Retrieve Relevant Information:** Based on the [USER_QUERY], identify the most relevant 
segments of one or many document from the [CONTEXT]. Focus on extracting direct answers and supporting 
details.

4.  **Generate Answer:** Synthesize the retrieved information into a clear, concise, and 
accurate answer to the [USER_QUERY].

5.  **Output JSON Response:** Format your response as a JSON object with the following 
structure:

    ```json
    {
      "response": "[Generated Answer with Citation Numbering]",
      "sources": [
        {
          "document_title": "[CONTEXT_DOCUMENT_NAME]",
          "section_text": "[Relevant Section/Paragraph Text]"
        }
      ]
    }
    ```

    *   `response`:  The generated answer to the user's question, including the citation 
number. Example: "The agreement assigns 3 Gen AI developers. [1]"
    *   `sources`: An array containing details about the source of the information. Each 
object in the array should include:
        *   `document_title`: The title of the document where the answer was found.
        *   `section_text`:  The exact text from the document that supports the answer.
        *   `success`: true/false based on either answered the question or not

6.  **Maintain Professional Tone:** Respond in a professional and informative tone.

7. **If the answer cannot be found within the context document, respond with:** "I'm sorry, I 
cannot answer that question based on the provided context document." 

8. ** the answer cannot be found within the context:
   - `sources` should be empty list: Example: sources: []
   - success should be false Example: success: false
   - No numbering will be added into the response

**Example:**

Success Example:
*   Response:
    ```json
    {
      "response": "<Markdown Response placeholder with citation number> [1]",
      "success": true,
      "sources": [
        {
          "document_title": [CONTEXT_DOCUMENT_NAME],
          "section_text": "[Relevant Section/Paragraph Text]"
        }
      ]
    }
    ```
Fail Example:
  ``json
      {
        "response": "I'm sorry, I cannot answer that question based on the available information I have.",
        "success": false,
        "sources": []
      }
  ```

**Important:** Always adhere to the specified JSON format. You must make sure you have responded with the keys `response`, `success`, and `sources`.
"""


USER_PROMPT_TEMPLATE = """
Context from documents:

[CONTEXT]: {context_content}

[USER_QUERY]: {query}

Your JSON response:
"""


class RAGChatAgent:
    """Agent that interfaces with vector database and LLM for RAG-based chat."""
    
    def __init__(
        self,
        llm_client: Ollama,
        vector_store: LanceDBVectorStore,
    ):
        """
        Initialize the RAG Chat Agent.
        
        Args:
            llm_client: Ollama LLM Client
            llm_model: Name of LLM model to use
        """
        
        # Initialize LLM client using llama_index Ollama
        self.llm_client = llm_client
        # Initialize vector store
        self.vector_store = vector_store
        logger.info(f"Initialized RAG Chat Agent with DB and LLM")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for documents matching the query.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of search results
        """
        try:
            results = self.vector_store.search(query, top_k=top_k)
            return results
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            raise

    
    def build_context(self, context_docs: List[Dict[str, Any]]) -> str:
        context = []
        for doc in context_docs:
            content = doc.get("content", "")
            file_name = doc.get("file_name", "")
            file_part = doc.get("chunk_id", "")
            context.append(f"--- [CONTEXT_DOCUMENT_NAME]: {file_name} [CONTEXT_DOCUMENT_NAME_PARTITION_NUMBER]: {file_part}) ---\n[CONTENT]:\n{content}\n\n")
        return "\n".join(context)
    

    def build_conversation_body(self, context) -> List[ChatMessage]:
        chat_messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=SYSTEM_PROMPT),
            ChatMessage(role=MessageRole.USER, content=context)
        ]
        return chat_messages

    def extract_json_response(self, response: str) -> Dict[str, Any]:
        json_match = re.search(r"```json\s*([\s\S]*?)\s*```", response)

        if json_match:
            try:
                parsed_response = json.loads(json_match.group(1))
                return parsed_response
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON from code block")
                parsed_response = {
                    "response": "Error: Failed to parse response format",
                    "success": False,
                    "sources": []
                    }
                return parsed_response
    
    def chat(
        self,
        query: str, 
    ) -> Dict[str, Any]:
        """
        Generate a RAG response using LLM based on query and context documents.
        
        Args:
            query: User query
            context_docs: Context documents from vector search
            chat_history: Optional chat history for context
            
        Returns:
            JSON response with answer and sources
        """
        docs = self.search(query)
        # Extract content from context documents
        context_content = self.build_context(docs)
        # Create prompt with context, history, and query
        prompt = USER_PROMPT_TEMPLATE.format(
            context_content=context_content,
            query=query
        )

        # Build conversation body
        chat_messages = self.build_conversation_body(prompt)
        
        try:
            # Generate response using LLM
            response = self.llm_client.chat(messages=chat_messages)
            return self.extract_json_response(response.message.content)
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return {
                "response": f"Error generating response: {str(e)}",
                "success": False,
                "sources": []
            }


if __name__ == "__main__":
    from procureme.clients.ollama_embedder import OllamaEmbeddingClient
    embed_client = OllamaEmbeddingClient()
    DBPATH = Path("vectordb").joinpath("contracts.db")
    vdb_table = "contracts_naive"
    vector_store = LanceDBVectorStore(db_path=DBPATH, table_name=vdb_table, embedding_client=embed_client)
    LLM_CLIENT = Ollama(model="gemma3:4b", request_timeout=120.0)
    agent = RAGChatAgent(llm_client=LLM_CLIENT, vector_store=vector_store)
    query="What do you know about Supplier: Alpha Suppliers Inc. and what it supplies?"
    # result = agent.search(query=query)
    response = agent.chat(query=query)
    print(response)
