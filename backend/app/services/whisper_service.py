"""Whisper STT (Speech-to-Text) service for audio transcription."""

from __future__ import annotations

import io
import logging
from typing import Optional

import openai

logger = logging.getLogger(__name__)


class WhisperService:
    """Speech-to-text transcription using OpenAI Whisper API."""

    def __init__(self, api_key: str, model: str = "whisper-1"):
        """
        Initialize Whisper service.

        Args:
            api_key: OpenAI API key
            model: Model to use (default: whisper-1)
        """
        self.api_key = api_key
        self.model = model
        openai.api_key = api_key

    async def transcribe(
        self,
        audio_data: bytes,
        language: str = "en",
        prompt: Optional[str] = None,
    ) -> dict:
        """
        Transcribe audio to text.

        Args:
            audio_data: Audio bytes (WAV, MP3, WebM, etc.)
            language: Language code (default: 'en')
            prompt: Optional prompt to guide transcription

        Returns:
            Dict with keys:
            - text (str): Transcribed text
            - language (str): Detected language
            - duration (float): Audio duration in seconds
            - confidence (float): Confidence score (0-1)
        """
        try:
            # Create file-like object for API
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "audio.webm"

            # Call Whisper API
            logger.info(
                f"Transcribing audio ({len(audio_data)} bytes) with language={language}"
            )

            # Use synchronous client (can be made async if needed)
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            
            transcript = client.audio.transcriptions.create(
                model=self.model,
                file=audio_file,
                language=language,
                prompt=prompt,
                response_format="verbose_json",
            )

            result = {
                "text": transcript.text,
                "language": getattr(transcript, "language", language),
                "duration": getattr(transcript, "duration", 0.0),
                "confidence": 0.95,  # Whisper doesn't return confidence, use default high
            }

            logger.info(f"Transcription successful: {len(result['text'])} chars")
            return result

        except openai.APIError as e:
            logger.error(f"Whisper API error: {str(e)}")
            raise Exception(f"Transcription failed: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error in transcribe: {str(e)}")
            raise Exception(f"Transcription failed: {str(e)}") from e

    async def transcribe_with_retries(
        self,
        audio_data: bytes,
        language: str = "en",
        max_retries: int = 2,
        prompt: Optional[str] = None,
    ) -> dict:
        """
        Transcribe with exponential backoff retry logic.

        Args:
            audio_data: Audio bytes
            language: Language code
            max_retries: Maximum number of retries
            prompt: Optional prompt

        Returns:
            Transcription result
        """
        import asyncio

        for attempt in range(max_retries + 1):
            try:
                return await self.transcribe(audio_data, language, prompt)
            except Exception as e:
                if attempt == max_retries:
                    logger.error(f"Transcription failed after {max_retries} retries")
                    raise

                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                logger.warning(
                    f"Transcription attempt {attempt + 1} failed, retrying in {wait_time}s: {str(e)}"
                )
                await asyncio.sleep(wait_time)
