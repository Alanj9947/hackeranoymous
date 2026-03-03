"""Conversation service orchestrating STT, LLM, and TTS pipeline."""

from __future__ import annotations

import logging
from typing import Optional, Dict, Any, List

from app.services.whisper_service import WhisperService
from app.services.openai_service import OpenAIService
from app.services.tts_service import TTSService

logger = logging.getLogger(__name__)


class ConversationService:
    """Orchestrates audio-to-audio AI conversation pipeline."""

    def __init__(
        self,
        openai_api_key: str,
        elevenlabs_api_key: str,
        openai_model: str = "gpt-4",
    ):
        """
        Initialize conversation service with AI services.

        Args:
            openai_api_key: OpenAI API key
            elevenlabs_api_key: ElevenLabs API key
            openai_model: OpenAI model to use
        """
        self.whisper = WhisperService(api_key=openai_api_key)
        self.openai = OpenAIService(api_key=openai_api_key, model=openai_model)
        self.tts = TTSService(api_key=elevenlabs_api_key)

    async def process_audio_chunk(
        self,
        audio_bytes: bytes,
        conversation_history: List[Dict[str, str]],
        agent_config: Dict[str, Any],
        language: str = "en",
    ) -> Dict[str, Any]:
        """
        Process audio through complete pipeline: STT → LLM → TTS.

        Args:
            audio_bytes: Audio data
            conversation_history: Previous messages
            agent_config: Agent configuration with system prompt, voice settings
            language: Audio language code

        Returns:
            Dict with:
            - transcript_user (str): User's transcribed text
            - response_text (str): Agent's response text
            - response_audio (bytes): Agent's response audio
            - latency_ms (float): Total processing time
        """
        import time

        start_time = time.time()
        result = {}

        try:
            # ── Step 1: Whisper STT ────────────────────────────────
            logger.info("Step 1: Starting speech-to-text...")
            stt_result = await self.whisper.transcribe(
                audio_bytes,
                language=language,
                prompt=agent_config.get("stt_prompt"),
            )
            transcript_user = stt_result["text"]
            logger.info(f"STT complete: '{transcript_user}'")
            result["transcript_user"] = transcript_user

            # ── Step 2: OpenAI LLM ─────────────────────────────────
            logger.info("Step 2: Generating AI response...")

            # Build conversation context
            messages = self.openai.build_conversation_history(
                conversation_history,
                transcript_user,
            )

            # Truncate to prevent token overflow
            messages = self.openai.truncate_messages(messages, max_messages=20)

            # Get system prompt from agent config
            system_prompt = agent_config.get("system_prompt", "You are a helpful assistant.")

            # Generate response
            response_text = await self.openai.chat_completion(
                messages=messages,
                system=system_prompt,
                temperature=agent_config.get("temperature", 0.7),
                max_tokens=agent_config.get("max_tokens", 500),
            )
            logger.info(f"LLM response: '{response_text}'")
            result["response_text"] = response_text

            # ── Step 3: ElevenLabs TTS ─────────────────────────────
            logger.info("Step 3: Synthesizing speech...")

            voice_id = agent_config.get("voice_id", "21m00Tcm4TlvDq8ikWAM")
            response_audio = await self.tts.synthesize(
                text=response_text,
                voice_id=voice_id,
                speed=agent_config.get("voice_speed", 1.0),
            )
            logger.info(f"TTS complete: {len(response_audio)} bytes")
            result["response_audio"] = response_audio

            # ── Metrics ────────────────────────────────────────────
            latency_ms = (time.time() - start_time) * 1000
            result["latency_ms"] = latency_ms
            logger.info(f"Complete pipeline latency: {latency_ms:.0f}ms")

            return result

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"Pipeline error after {latency_ms:.0f}ms: {str(e)}")
            raise Exception(f"Audio processing failed: {str(e)}") from e

    async def process_audio_chunk_with_fallback(
        self,
        audio_bytes: bytes,
        conversation_history: List[Dict[str, str]],
        agent_config: Dict[str, Any],
        language: str = "en",
    ) -> Dict[str, Any]:
        """
        Process audio with fallback: if TTS fails, return text only.

        Args:
            audio_bytes: Audio data
            conversation_history: Previous messages
            agent_config: Agent configuration
            language: Audio language code

        Returns:
            Dict with transcript and response (audio optional)
        """
        try:
            return await self.process_audio_chunk(
                audio_bytes,
                conversation_history,
                agent_config,
                language,
            )
        except Exception as e:
            logger.warning(f"Full pipeline failed, attempting text-only fallback: {str(e)}")

            # Fallback: Try STT and LLM without TTS
            try:
                stt_result = await self.whisper.transcribe(
                    audio_bytes,
                    language=language,
                )
                transcript_user = stt_result["text"]

                messages = self.openai.build_conversation_history(
                    conversation_history,
                    transcript_user,
                )
                messages = self.openai.truncate_messages(messages, max_messages=20)

                system_prompt = agent_config.get(
                    "system_prompt", "You are a helpful assistant."
                )

                response_text = await self.openai.chat_completion(
                    messages=messages,
                    system=system_prompt,
                    temperature=agent_config.get("temperature", 0.7),
                    max_tokens=agent_config.get("max_tokens", 500),
                )

                logger.info("Fallback to text-only response successful")
                return {
                    "transcript_user": transcript_user,
                    "response_text": response_text,
                    "response_audio": None,
                    "fallback": True,
                    "error": str(e),
                }

            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {str(fallback_error)}")
                raise Exception(
                    f"All processing attempts failed: {str(fallback_error)}"
                ) from fallback_error

    async def get_agent_system_prompt(
        self, agent_config: Dict[str, Any]
    ) -> str:
        """
        Extract and build system prompt from agent config.

        Args:
            agent_config: Agent configuration

        Returns:
            System prompt string
        """
        system_config = agent_config.get("system_prompt", {})

        if isinstance(system_config, str):
            return system_config

        # Build from components
        parts = []

        # Personality
        if isinstance(system_config, dict):
            personality = system_config.get("personality")
            if personality:
                parts.append(f"Your personality: {personality}")

            # Goals
            goals = system_config.get("goals", [])
            if goals:
                goals_text = "\n".join([f"- {goal}" for goal in goals])
                parts.append(f"Your goals:\n{goals_text}")

            # Environment
            environment = system_config.get("environment")
            if environment:
                parts.append(f"Environment: {environment}")

            # Constraints
            constraints = system_config.get("constraints", [])
            if constraints:
                constraints_text = "\n".join([f"- {c}" for c in constraints])
                parts.append(f"Constraints:\n{constraints_text}")

            # Tone
            tone = system_config.get("tone")
            if tone:
                parts.append(f"Tone: {tone}")

        if parts:
            return "\n".join(parts)

        return "You are a helpful assistant."
