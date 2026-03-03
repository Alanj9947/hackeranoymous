"""
Speech-to-Text service using OpenAI Whisper.
"""

from __future__ import annotations

import io
import tempfile

import openai

from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

_client = None


def _get_client() -> openai.AsyncOpenAI:
    global _client
    if _client is None:
        _client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


async def transcribe_audio_chunk(audio_data: bytes, language: str = "en") -> str:
    """
    Transcribe raw audio bytes (mulaw 8kHz from Twilio) using Whisper.
    Returns the transcribed text.
    """
    try:
        client = _get_client()

        # Write audio to a temp file (Whisper API needs a file-like object)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
            # Convert mulaw to WAV format header + data
            _write_wav_header(tmp, audio_data, sample_rate=8000, channels=1, bits_per_sample=8)
            tmp.write(audio_data)
            tmp.seek(0)

            response = await client.audio.transcriptions.create(
                model=settings.OPENAI_WHISPER_MODEL,
                file=("audio.wav", tmp, "audio/wav"),
                language=language,
                response_format="text",
            )

        text = response.strip() if isinstance(response, str) else response.text.strip()
        return text

    except Exception as e:
        logger.error("stt_error", error=str(e))
        return ""


def _write_wav_header(
    f, data: bytes, sample_rate: int = 8000, channels: int = 1, bits_per_sample: int = 8
):
    """Write a minimal WAV file header."""
    import struct

    data_size = len(data)
    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8

    f.write(b"RIFF")
    f.write(struct.pack("<I", 36 + data_size))
    f.write(b"WAVE")
    f.write(b"fmt ")
    f.write(struct.pack("<I", 16))  # chunk size
    f.write(struct.pack("<H", 7))  # format: mulaw
    f.write(struct.pack("<H", channels))
    f.write(struct.pack("<I", sample_rate))
    f.write(struct.pack("<I", byte_rate))
    f.write(struct.pack("<H", block_align))
    f.write(struct.pack("<H", bits_per_sample))
    f.write(b"data")
    f.write(struct.pack("<I", data_size))


async def transcribe_file(file_path: str, language: str = "en") -> str:
    """Transcribe a full audio file (for post-call processing)."""
    try:
        client = _get_client()
        with open(file_path, "rb") as f:
            response = await client.audio.transcriptions.create(
                model=settings.OPENAI_WHISPER_MODEL,
                file=f,
                language=language,
                response_format="verbose_json",
                timestamp_granularities=["segment"],
            )
        return response
    except Exception as e:
        logger.error("stt_file_error", error=str(e), file=file_path)
        return None
