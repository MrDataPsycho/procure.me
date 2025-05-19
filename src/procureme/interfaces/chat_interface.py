from llama_index.llms.ollama import Ollama
from llama_index.core.llms import ChatMessage
from pydantic import BaseModel
import json
import re
from typing import List, Dict, Optional, Self
from enum import StrEnum
import logging


# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set the logging level to DEBUG for detailed information
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log message format
    handlers=[
        logging.StreamHandler(),  # Output to console
        # logging.FileHandler("commodity_code_matcher.log", mode='w')  # Output to file
    ],
)

logger = logging.getLogger(__name__)

logger.info("Loading LLM...")


class ModelSelection(StrEnum):
    """Enum for selecting the available LLM models."""

    PHI3_5 = "phi3.5:latest"
    LLAMA3_1 = "llama3.1:latest"


class CommodityCode(BaseModel):
    """Represents a single commodity code with its associated confidence score."""

    code: int
    confidence: int


class CommodityCodeList(BaseModel):
    """Represents a list of commodity codes and provides utility methods."""

    results: List[CommodityCode]

    def get_all_codes(self) -> List[int]:
        """Retrieve all commodity code IDs from the result list."""
        return [item.code for item in self.results]

    def get_key_value_pairs(self) -> Dict[int, int]:
        """Retrieve a dictionary of commodity codes and their confidence scores."""
        return {item.code: item.confidence for item in self.results}

    @classmethod
    def from_json_string(cls, json_str: str) -> Self:
        """
        Factory method to create a CommodityCodeList instance from a JSON string.

        Args:
            json_str (str): The JSON string representing the list of commodity codes.

        Returns:
            CommodityCodeList: A new instance of CommodityCodeList.
        """
        logger.info(f"Received string as JSON: {json_str}")
        response_dict = CommodityCodeMatcher.extract_json_from_markdown(json_str)
        if response_dict:
            return cls(results=[CommodityCode(**item) for item in response_dict])
        return cls(results=[])


class CommodityCodeMatcher:
    """Service class to handle matching queries against commodity codes."""

    def __init__(
        self, model_name: ModelSelection = ModelSelection.PHI3_5, timeout: int = 120
    ):
        """Initialize the matcher with the model name and request timeout."""
        self.llm = Ollama(
            model=str(model_name), request_timeout=timeout, temperature=0.0
        )

    def get_commodity_codes(self, query: str, context: str) -> CommodityCodeList:
        """
        Get a list of commodity codes based on a user query and context.

        Args:
            query (str): The user query.
            context (str): The commodity codes and descriptions context.

        Returns:
            CommodityCodeList: A list of matched commodity codes with confidence scores.
        """
        logger.info(f"Query received: {query}")
        logger.info(f"Context glimps: {context[:100]}")
        system_prompt = self._generate_system_prompt()
        user_prompt = self._generate_user_prompt(query, context)

        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_prompt),
        ]
        response = self.llm.chat(messages)
        return CommodityCodeList.from_json_string(response.message.content)

    @staticmethod
    def extract_json_from_markdown(markdown_content: str) -> Optional[List[Dict]]:
        """
        Extract JSON content from a markdown-formatted string.

        Args:
            markdown_content (str): The string containing markdown with JSON content.

        Returns:
            Optional[List[Dict]]: The extracted JSON object if valid, otherwise None.
        """
        json_pattern = r"```json\n(.*?)\n```"
        match = re.search(json_pattern, markdown_content, re.DOTALL)
        if match:
            json_content = match.group(1)
            try:
                return json.loads(json_content)
            except json.JSONDecodeError:
                return None
        return None

    @staticmethod
    def _generate_system_prompt() -> str:
        """Generate the system prompt to instruct the model."""
        return """You are a helpful assistant designed to match user queries with relevant commodity codes with descriptions as context used in procurement purchase orders.
        You will go through the description provided for each commodity code and try to match the user's query with top 3 relevant commodity codes.
        You must always respond with a valid JSON array of objects where each object contains:
        1. "code": The ID of the commodity code (as a string).
        2. "confidence": A number from 0 to 100 indicating your confidence that the commodity code matches the user's query.
        3. code and confidence both should be integers.
        4. You should go through all the descriptions and then decide which commodity code matches the user's query.
        5. Make sure you filter the commodity codes that are not relevant to the user's query and having confidence less than 50
        The JSON format should look like this wrapped with markdown code block:
        ```json
        [
            {"code": 10001, "confidence": 80},
            {"code": 10002, "confidence": 60},
            ...
        ]
        ```
        If no commodity code matches the query, return an empty array.
        After you prepared the JSON you must validate it to ensure it is valid and wrapped with markdown code block.
        Please, plase Do not add any extra text in the beginning or end of the JSON in your response.
        Please do not add any Validation: description ar the end of the JSON.
        """

    @staticmethod
    def _generate_user_prompt(query: str, context: str) -> str:
        """Generate the user prompt with the provided query and context."""
        return f"Query:\n{query}\n\nContext:\n{context}\n"


# Example usage
if __name__ == "__main__":
    context = """
    1. 10001 - Computer, Hardware
    2. 10002 - Software for Computer
    3. 10003 - Office Furniture
    4. 10004 - Computer Accessories
    5. 10005 - Office Supplies
    """
    query = "I want to buy a keyboard and mouse."

    matcher = CommodityCodeMatcher(ModelSelection.LLAMA3_1)
    commodity_codes = matcher.get_commodity_codes(query=query, context=context)

    print(commodity_codes.get_all_codes())
    print(commodity_codes.get_key_value_pairs())
