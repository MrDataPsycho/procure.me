import httpx
from typing import Optional, List, Dict, Any


class ChatSessionClient:
    """
    A client for interacting with the Procure.Me chat session backend.

    Attributes:
        base_url (str): The base URL of the chat session endpoint.
        client (httpx.Client): An HTTPX client instance for making API calls.
    """

    def __init__(self, base_url: str):
        """
        Initialize the ChatSessionClient.

        Args:
            base_url (str): The base URL of the chat session API.
        """
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(base_url=self.base_url)

    def create_session(self, label: str) -> Optional[Dict[str, Any]]:
        """
        Create a new chat session with a given label.

        Args:
            label (str): The label of the new chat session.

        Returns:
            dict: The created chat session object, or None if the request failed.
        """
        response = self.client.post("/", params={"label": label})
        if response.status_code == 200:
            return response.json()
        return None

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a chat session by its ID.

        Args:
            session_id (str): UUID of the chat session.

        Returns:
            dict: The chat session data if found, else None.
        """
        response = self.client.get(f"/{session_id}")
        if response.status_code == 200:
            return response.json()
        return None

    def update_session_label(self, session_id: str, label: str) -> Optional[Dict[str, Any]]:
        """
        Rename a chat session.

        Args:
            session_id (str): UUID of the chat session.
            label (str): New label for the session.

        Returns:
            dict: The updated chat session data, or None if failed.
        """
        response = self.client.patch(f"/{session_id}", params={"label": label})
        if response.status_code == 200:
            return response.json()
        return None

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a chat session.

        Args:
            session_id (str): UUID of the session to delete.

        Returns:
            bool: True if deletion succeeded, False otherwise.
        """
        response = self.client.delete(f"/{session_id}")
        return response.status_code == 200 and response.json().get("success", False)

    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        Retrieve a list of all sessions with minimal metadata.

        Returns:
            List[dict]: A list of chat sessions, each containing at least the ID and label.
        """
        response = self.client.get("/")
        if response.status_code == 200:
            return response.json()
        return []

    def send_chat(self, session_id: str, query: str) -> Optional[Dict[str, Any]]:
        """
        Send a user query to the chat and receive a response.

        Args:
            session_id (str): UUID of the chat session.
            query (str): The user's message or question.

        Returns:
            dict: The assistant's response and sources, or None if failed.
        """
        payload = {"session_id": session_id, "query": query}
        response = self.client.post("/chat", json=payload)
        if response.status_code == 200:
            return response.json()
        return None
