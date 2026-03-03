"""
Text-to-Speech service supporting ElevenLabs, Azure, and OpenAI.
"""

from __future__ import annotations

from typing import Optional

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


async def synthesize_speech(
    text: str,
    provider: str = "elevenlabs",
    voice_id: Optional[str] = None,
    speed: float = 1.0,
) -> Optional[bytes]:
    """
    Convert text to audio bytes using the configured TTS provider.
    Returns raw audio bytes (mp3/pcm depending on provider).
    """
    try:
        if provider == "elevenlabs":
            return await _elevenlabs_tts(text, voice_id or settings.ELEVENLABS_VOICE_ID, speed)
        elif provider == "openai":
            return await _openai_tts(text, voice_id or "alloy", speed)
        elif provider == "azure":
            return await _azure_tts(text, voice_id)
        else:
            logger.warning("unknown_tts_provider", provider=provider)
            return await _openai_tts(text, "alloy", speed)
    except Exception as e:
        logger.error("tts_error", provider=provider, error=str(e))
        return None


async def _elevenlabs_tts(text: str, voice_id: str, speed: float = 1.0) -> bytes:
    """ElevenLabs TTS API."""
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={
                "xi-api-key": settings.ELEVENLABS_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "style": 0.0,
                    "use_speaker_boost": True,
                },
                "output_format": "ulaw_8000",  # Twilio-compatible
            },
        )
        response.raise_for_status()
        return response.content


async def _openai_tts(text: str, voice: str = "alloy", speed: float = 1.0) -> bytes:
    """OpenAI TTS API."""
    import openai

    client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    response = await client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text,
        speed=speed,
        response_format="pcm",
    )
    return response.content


async def _azure_tts(text: str, voice_name: Optional[str] = None) -> bytes:
    """Azure Cognitive Services TTS."""
    if not settings.AZURE_SPEECH_KEY:
        raise ValueError("Azure Speech key not configured")

    voice = voice_name or "en-US-JennyNeural"
    ssml = f"""
    <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>
        <voice name='{voice}'>{text}</voice>
    </speak>
    """

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"https://{settings.AZURE_SPEECH_REGION}.tts.speech.microsoft.com"
            "/cognitiveservices/v1",
            headers={
                "Ocp-Apim-Subscription-Key": settings.AZURE_SPEECH_KEY,
                "Content-Type": "application/ssml+xml",
                "X-Microsoft-OutputFormat": "raw-8khz-8bit-mono-mulaw",
            },
            content=ssml,
        )
        response.raise_for_status()
        return response.content
