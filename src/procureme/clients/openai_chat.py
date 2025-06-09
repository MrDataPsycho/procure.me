from procureme.configurations.aimodels import ChatModelSelection
from openai import OpenAI, AsyncOpenAI
import logging
from openai import RateLimitError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class OpenAIClient:
    def __init__(self, api_key: str, model=ChatModelSelection.GPT3):
        self.api_key = api_key
        self.model= model
        self.openai = OpenAI(api_key=api_key)
        self.async_openai = AsyncOpenAI(api_key=api_key)

    @retry(
    retry=retry_if_exception_type(RateLimitError),
    wait=wait_exponential(multiplier=1, min=5, max=60),
    stop=stop_after_attempt(6),
    reraise=True
    )
    def chat(self, messages: list[dict], temperature=0, config={}) -> str:
        """Chat with OpenAI API.

        Args:
            messages (list[dict]): List of messages to send to OpenAI API.
            temperature (float, optional): Temperature to use for OpenAI API. Defaults to 0.
            config (dict, optional): Additional configuration to use for OpenAI API. Defaults to {}.

        Returns:
            str: Response from OpenAI API.
        """
        response = self.openai.chat.completions.create(
            model=self.model,
            temperature=temperature,
            messages=messages,
            **config,
        )
        logger.info(f"Chat endpoint called with Model {self.model}, Request: {messages[-1]}")
        content = response.choices[0].message.content.strip()
        return content
    
    @retry(
    retry=retry_if_exception_type(RateLimitError),
    wait=wait_exponential(multiplier=1, min=5, max=60),
    stop=stop_after_attempt(6),
    reraise=True
    )
    async def chat_async(self, messages, temperature=0, config={}) -> str:
        """Chat with OpenAI API.

        Args:
            messages (list[dict]): List of messages to send to OpenAI API.
            temperature (float, optional): Temperature to use for OpenAI API. Defaults to 0.
            config (dict, optional): Additional configuration to use for OpenAI API. Defaults to {}.

        Returns:
            str: Response from OpenAI API.
        """
        response = await self.async_openai.chat.completions.create(
            model=self.model,
            temperature=temperature,
            messages=messages,
            **config,
        )
        logger.info(f"Chat endpoint called with Model {self.model}, Request: {messages[-1]}")
        content = response.choices[0].message.content.strip()
        return content
    

    @retry(
    retry=retry_if_exception_type(RateLimitError),
    wait=wait_exponential(multiplier=1, min=5, max=60),
    stop=stop_after_attempt(6),
    reraise=True
    )
    def select_tool(self, messages: list[dict], temperature=0, tools=[], config={}):
        """Select tool with OpenAI API.

        Args:
            messages (list[dict]): List of messages to send to OpenAI API.
            temperature (float, optional): Temperature to use for OpenAI API. Defaults to 0.
            config (dict, optional): Additional configuration to use for OpenAI API. Defaults to {}.

        Returns:
            Any: Response from OpenAI API.
        """
        response = self.openai.chat.completions.create(
            model=self.model,
            temperature=temperature,
            messages=messages,
            tools=tools or None,
            **config,
        )
        tools = response.choices[0].message.tool_calls
        return tools
    

    @retry(
    retry=retry_if_exception_type(RateLimitError),
    wait=wait_exponential(multiplier=1, min=5, max=60),
    stop=stop_after_attempt(6),
    reraise=True
    )
    async def select_tool_async(self, messages: list[dict], temperature=0, tools=[], config={}):
        """Select tool with OpenAI API.

        Args:        
            messages (list[dict]): List of messages to send to OpenAI API.    
            temperature (float, optional): Temperature to use for OpenAI API. Defaults to 0.
            config (dict, optional): Additional configuration to use for OpenAI API. Defaults to {}.

        Returns:
            Any: Response from OpenAI API.
        """
        response = self.async_openai.chat.completions.create(
            model=self.model,
            temperature=temperature,
            messages=messages,
            tools=tools or None,
            **config,
        )
        tools = response.choices[0].message.tool_calls
        return tools

    def __repr__(self):
        return f"OpenAIClient(api_key=***, model={self.model})"

    def __str__(self):
        return f"OpenAIClient(api_key=***, model={self.model})"
