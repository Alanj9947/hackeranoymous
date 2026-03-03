"""OpenAI LLM service for conversation AI responses."""

from __future__ import annotations

import logging
from typing import Optional, List, Dict, Any, AsyncIterator

import openai

logger = logging.getLogger(__name__)


class OpenAIService:
    """Large Language Model service using OpenAI GPT-4 API."""

    def __init__(self, api_key: str, model: str = "gpt-4"):
        """
        Initialize OpenAI service.

        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-4)
        """
        self.api_key = api_key
        self.model = model
        openai.api_key = api_key

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        """
        Generate chat completion response.

        Args:
            messages: List of messages with 'role' and 'content'
            system: System prompt to guide behavior
            temperature: Response randomness (0-2, default 0.7)
            max_tokens: Maximum tokens in response

        Returns:
            Generated response text
        """
        try:
            # Build message list with system prompt if provided
            if system:
                full_messages = [{"role": "system", "content": system}] + messages
            else:
                full_messages = messages

            logger.info(
                f"Generating completion with {self.model}: "
                f"{len(messages)} messages, temp={temperature}, max_tokens={max_tokens}"
            )

            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)

            response = client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=30.0,
            )

            result = response.choices[0].message.content
            logger.info(
                f"Completion successful: {len(result)} chars, "
                f"usage: {response.usage.total_tokens} tokens"
            )
            return result

        except openai.APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise Exception(f"Chat completion failed: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error in chat_completion: {str(e)}")
            raise Exception(f"Chat completion failed: {str(e)}") from e

    async def stream_response(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> AsyncIterator[str]:
        """
        Stream chat completion response tokens.

        Args:
            messages: List of messages
            system: System prompt
            temperature: Response randomness
            max_tokens: Maximum tokens

        Yields:
            Response tokens as they're generated
        """
        try:
            if system:
                full_messages = [{"role": "system", "content": system}] + messages
            else:
                full_messages = messages

            logger.info(f"Starting stream with {len(messages)} messages")

            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)

            stream = client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                timeout=30.0,
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

            logger.info("Stream completed")

        except Exception as e:
            logger.error(f"Error in stream_response: {str(e)}")
            raise Exception(f"Stream failed: {str(e)}") from e

    def build_conversation_history(
        self,
        messages: List[Dict[str, str]],
        user_message: str,
    ) -> List[Dict[str, str]]:
        """
        Build conversation history with new user message.

        Args:
            messages: Previous messages (alternating user/assistant)
            user_message: Latest user message

        Returns:
            Updated message list
        """
        # Convert DB format to OpenAI format if needed
        openai_messages = []

        for msg in messages:
            if isinstance(msg, dict) and "speaker" in msg:
                # From database format
                role = "user" if msg["speaker"] == "user" else "assistant"
                openai_messages.append({"role": role, "content": msg["message"]})
            else:
                # Already in OpenAI format
                openai_messages.append(msg)

        # Add new user message
        openai_messages.append({"role": "user", "content": user_message})

        return openai_messages

    @staticmethod
    def truncate_messages(
        messages: List[Dict[str, str]],
        max_messages: int = 20,
    ) -> List[Dict[str, str]]:
        """
        Truncate conversation history to prevent token overflow.

        Args:
            messages: Full message list
            max_messages: Maximum messages to keep

        Returns:
            Truncated message list (keeps most recent)
        """
        if len(messages) <= max_messages:
            return messages

        # Keep first system message + most recent messages
        if messages[0].get("role") == "system":
            return [messages[0]] + messages[-max_messages + 1 :]
        else:
            return messages[-max_messages:]
