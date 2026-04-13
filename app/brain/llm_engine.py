"""
Ollama LLM Engine — streaming chat interface for the AI agent brain.
"""

import logging
from typing import AsyncGenerator, List, Optional

from ollama import AsyncClient, ChatResponse

from app.config import settings

logger = logging.getLogger(__name__)


class LLMEngine:
    """Async Ollama LLM interface with streaming support."""

    def __init__(self, model: Optional[str] = None, base_url: Optional[str] = None):
        self.model = model or settings.OLLAMA_MODEL
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self._client = AsyncClient(host=self.base_url)

    async def chat(self, user_message: str, system_prompt: str = "",
                   history: Optional[List[dict]] = None) -> str:
        """
        Send a message and get the full response (non-streaming).

        Args:
            user_message: The user's input text.
            system_prompt: System prompt for personality/context.
            history: Previous conversation messages.

        Returns:
            The complete LLM response text.
        """
        messages = self._build_messages(user_message, system_prompt, history)

        try:
            response: ChatResponse = await self._client.chat(
                model=self.model,
                messages=messages,
                options={"temperature": 0.7},
            )
            return response.message.content
        except Exception as e:
            logger.error(f"LLM chat error: {e}")
            return f"I'm sorry, I encountered an error: {str(e)}"

    async def chat_stream(self, user_message: str, system_prompt: str = "",
                          history: Optional[List[dict]] = None) -> AsyncGenerator[str, None]:
        """
        Send a message and stream the response token-by-token.

        Args:
            user_message: The user's input text.
            system_prompt: System prompt for personality/context.
            history: Previous conversation messages.

        Yields:
            Individual response tokens/chunks.
        """
        messages = self._build_messages(user_message, system_prompt, history)

        try:
            stream = await self._client.chat(
                model=self.model,
                messages=messages,
                stream=True,
                options={"temperature": 0.7},
            )
            async for chunk in stream:
                if chunk.message.content:
                    yield chunk.message.content
        except Exception as e:
            logger.error(f"LLM stream error: {e}")
            yield f"I'm sorry, I encountered an error: {str(e)}"

    async def chat_for_tools(self, user_message: str, system_prompt: str = "",
                             history: Optional[List[dict]] = None) -> str:
        """
        Chat with temperature=0 for deterministic tool-calling output.
        Used when we expect the LLM to return structured JSON actions.
        """
        messages = self._build_messages(user_message, system_prompt, history)

        try:
            response: ChatResponse = await self._client.chat(
                model=self.model,
                messages=messages,
                options={"temperature": 0},
            )
            return response.message.content
        except Exception as e:
            logger.error(f"LLM tool-call error: {e}")
            return f"I'm sorry, I encountered an error: {str(e)}"

    def _build_messages(self, user_message: str, system_prompt: str = "",
                        history: Optional[List[dict]] = None) -> List[dict]:
        """Build the message list for the LLM."""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if history:
            messages.extend(history)

        messages.append({"role": "user", "content": user_message})
        return messages

    async def check_connection(self) -> bool:
        """Check if Ollama is reachable and the model is available."""
        try:
            models = await self._client.list()
            available = [m.model for m in models.models]
            if self.model in available or any(self.model in m for m in available):
                logger.info(f"Ollama connected. Model '{self.model}' available.")
                return True
            else:
                logger.warning(f"Model '{self.model}' not found. Available: {available}")
                return False
        except Exception as e:
            logger.error(f"Ollama connection failed: {e}")
            return False
