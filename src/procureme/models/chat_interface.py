#!/usr/bin/env python
# coding: utf-8

# In[74]:


get_ipython().system(
    "jupyter nbconvert ollama-with-openai.ipynb --to python --output ../src/smart_procurement/models/chat_interface.py"
)


# In[27]:


from llama_index.llms.ollama import Ollama
from typing import Self


# In[2]:


llm = Ollama(model="llama3.1:latest", request_timeout=120.0)


# In[55]:


SYSTEM_PROMPT = """You are a helpful assistant designed to match user queries with relevant commodity codes with descriptions as context used in procurement purchase orders.
You will go through the description provided for each commodity code and try to match the user's query with atleast top 3 relevant commodity codes.
You must always respond with a valid JSON array of objects where each object contains:
1. "code": The ID of the commodity code (as a string).
2. "confidence": A number from 0 to 100 indicating your confidence that the commodity code matches the user's query.
3. code and confidence both should be integers.
4. You should go through all the descriptions and then decide which commodity code matches the user's query.

The JSON format should look like this wrapped with markdown code block:
```json
[
    {"code": 10001, "confidence": 80},
    {"code": 10002, "confidence": 60},
    ...
]
```
Only include the commodity codes that have a relevance or confidence above 30. 
If no commodity code matches the query, return an empty array.

Always ensure the JSON response is valid.
After you prepared the json you must validate it that is a valid json and return it to user.
Provide me only the JSON and nothing else. Do not add any extra text in the beginning or end of the JSON.
"""


# In[56]:


CONTEXT = """
1. 10001 - Computer, Hardware
2. 10002 - Software for Computer
3. 10003 - Office Furniture
4. 10004 - Computer Accessories
5. 10005 - Office Supplies
"""

QUERY = "I want to buy a keyboard and mouse."


# In[57]:


USER_PROMPT = f"""Query:\n{QUERY} \n\n Context:\n{CONTEXT}\n"""


# In[70]:


from llama_index.core.llms import ChatMessage

messages = [
    ChatMessage(
        role="system",
        content=SYSTEM_PROMPT,
    ),
    ChatMessage(role="user", content=USER_PROMPT),
]


# In[71]:


resp = llm.chat(messages)


# In[60]:


import json
import re


def extract_json_from_markdown(markdown_content):
    # Regular expression to find JSON content between markdown code block
    json_pattern = r"```json\n(.*?)\n```"
    match = re.search(json_pattern, markdown_content, re.DOTALL)

    if match:
        json_content = match.group(1)
        try:
            # Parse and return the JSON object
            return json.loads(json_content)
        except json.JSONDecodeError:
            return None
    return None


# In[72]:


extract_json_from_markdown(resp.message.content)


# In[62]:


from pydantic import BaseModel


# In[63]:


class CommodityCodeResult(BaseModel):
    code: int
    confidence: int


# In[64]:


class CommodityCodeResultList(BaseModel):
    results: list[CommodityCodeResult]

    def get_all_codes(self) -> list[int]:
        if self.results:
            return [int(item.code) for item in self.results]
        return []

    @classmethod
    def from_model_response_str(cls, response_str: str) -> Self:
        response_dict = extract_json_from_markdown(response_str)
        if response_dict:
            return cls(results=[CommodityCodeResult(**item) for item in response_dict])
        return cls(results=[])

    def get_key_value_pairs(self) -> dict[int, int]:
        return {item.code: item.confidence for item in self.results}


# In[65]:


commodit_codes = CommodityCodeResultList.from_model_response_str(resp.message.content)


# In[66]:


commodit_codes.get_all_codes()


# In[77]:


from enum import StrEnum


class ModelSelection(StrEnum):
    """Enum for selecting the available LLM models."""

    PHI3_5 = "phi3.5:latest"
    LLAMA3_1 = "llama3.1:latest"


str(ModelSelection.PHI3_5)
