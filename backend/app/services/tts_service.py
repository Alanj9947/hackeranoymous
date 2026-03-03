"""ElevenLabs TTS (Text-to-Speech) service for voice synthesis."""

from __future__ import annotations

import logging
from typing import Optional, AsyncIterator

logger = logging.getLogger(__name__)


class TTSService:
    """Text-to-speech synthesis using ElevenLabs API."""

    def __init__(self, api_key: str, base_url: str = "https://api.elevenlabs.io/v1"):
        """
        Initialize TTS service.

        Args:
            api_key: ElevenLabs API key
            base_url: API base URL (default: official)
        """
        self.api_key = api_key
        self.base_url = base_url

    async def synthesize(
        self,
        text: str,
        voice_id: str = "21m00Tcm4TlvDq8ikWAM",  # Default ElevenLabs voice
        speed: float = 1.0,
    ) -> bytes:
        """
        Synthesize text to speech.

        Args:
            text: Text to synthesize
            voice_id: ElevenLabs voice ID
            speed: Playback speed (0.5-2.0, default 1.0)

        Returns:
            Audio bytes (MP3 format)
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        if len(text) > 5000:
            logger.warning(f"Text length {len(text)} exceeds recommended 5000 chars")

        try:
            import aiohttp

            logger.info(
                f"Synthesizing TTS: {len(text)} chars, voice={voice_id}, speed={speed}"
            )

            headers = {"xi-api-key": self.api_key}
            payload = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                },
            }

            url = f"{self.base_url}/text-to-speech/{voice_id}"

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"TTS API error: {response.status} - {error_text}")
                        raise Exception(
                            f"TTS synthesis failed: {response.status} - {error_text}"
                        )

                    audio_data = await response.read()
                    logger.info(f"TTS synthesis successful: {len(audio_data)} bytes")
                    return audio_data

        except Exception as e:
            logger.error(f"Error in synthesize: {str(e)}")
            raise Exception(f"TTS synthesis failed: {str(e)}") from e

    async def stream(
        self,
        text: str,
        voice_id: str = "21m00Tcm4TlvDq8ikWAM",
        speed: float = 1.0,
        chunk_size: int = 4096,
    ) -> AsyncIterator[bytes]:
        """
        Stream TTS audio in chunks.

        Args:
            text: Text to synthesize
            voice_id: ElevenLabs voice ID
            speed: Playback speed
            chunk_size: Chunk size for streaming

        Yields:
            Audio bytes chunks
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        try:
            import aiohttp

            logger.info(f"Starting TTS stream: {len(text)} chars")

            headers = {"xi-api-key": self.api_key}
            payload = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                },
            }

            url = f"{self.base_url}/text-to-speech/{voice_id}/stream"

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"TTS stream error: {response.status} - {error_text}")
                        raise Exception(f"TTS stream failed: {response.status}")

                    # Stream the response in chunks
                    async for chunk in response.content.iter_chunked(chunk_size):
                        if chunk:
                            yield chunk

            logger.info("TTS stream completed")

        except Exception as e:
            logger.error(f"Error in stream: {str(e)}")
            raise Exception(f"TTS stream failed: {str(e)}") from e

    @staticmethod
    def validate_text(text: str) -> bool:
        """
        Validate text for TTS synthesis.

        Args:
            text: Text to validate

        Returns:
            True if valid, False otherwise
        """
        if not text or not isinstance(text, str):
            return False
        if len(text.strip()) == 0:
            return False
        if len(text) > 5000:
            return False
        return True

    @staticmethod
    def split_long_text(text: str, max_length: int = 1000) -> list[str]:
        """
        Split long text into chunks for processing.

        Args:
            text: Long text to split
            max_length: Maximum length per chunk

        Returns:
            List of text chunks
        """
        if len(text) <= max_length:
            return [text]

        chunks = []
        current_chunk = ""

        for sentence in text.split(". "):
            if len(current_chunk) + len(sentence) + 2 <= max_length:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks
