"""Call recording service for storing and managing audio recordings."""

from __future__ import annotations

import io
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID

logger = logging.getLogger(__name__)


class CallRecordingService:
    """Service for recording, storing, and retrieving call recordings."""

    def __init__(self, storage_path: str = "/tmp/recordings"):
        """
        Initialize recording service.

        Args:
            storage_path: Local path for storing recordings
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Recording service initialized with path: {self.storage_path}")

    async def save_call_recording(
        self,
        conversation_id: UUID,
        audio_data: bytes,
        format: str = "mp3",
    ) -> dict:
        """
        Save call recording to storage.

        Args:
            conversation_id: Unique conversation ID
            audio_data: Audio bytes
            format: Audio format (mp3, wav, webm)

        Returns:
            Dict with:
            - file_path (str): Local file path
            - url (str): Public URL (if configured)
            - size_bytes (int): File size
            - created_at (str): Creation timestamp
        """
        try:
            if not audio_data:
                raise ValueError("Audio data cannot be empty")

            # Generate filename
            filename = f"{conversation_id}.{format}"
            file_path = self.storage_path / filename

            # Write to disk
            file_path.write_bytes(audio_data)
            logger.info(f"Recording saved: {file_path} ({len(audio_data)} bytes)")

            result = {
                "file_path": str(file_path),
                "url": f"/api/v1/calls/{conversation_id}/recording",
                "size_bytes": len(audio_data),
                "created_at": datetime.utcnow().isoformat(),
                "format": format,
            }

            return result

        except Exception as e:
            logger.error(f"Error saving recording: {str(e)}")
            raise Exception(f"Failed to save recording: {str(e)}") from e

    async def get_recording(
        self,
        conversation_id: UUID,
        format: str = "mp3",
    ) -> Optional[bytes]:
        """
        Retrieve recording from storage.

        Args:
            conversation_id: Conversation ID
            format: Audio format

        Returns:
            Audio bytes or None if not found
        """
        try:
            filename = f"{conversation_id}.{format}"
            file_path = self.storage_path / filename

            if not file_path.exists():
                logger.warning(f"Recording not found: {file_path}")
                return None

            audio_data = file_path.read_bytes()
            logger.info(f"Recording retrieved: {len(audio_data)} bytes")
            return audio_data

        except Exception as e:
            logger.error(f"Error retrieving recording: {str(e)}")
            return None

    async def delete_recording(
        self,
        conversation_id: UUID,
        format: str = "mp3",
    ) -> bool:
        """
        Delete recording from storage.

        Args:
            conversation_id: Conversation ID
            format: Audio format

        Returns:
            True if deleted, False if not found
        """
        try:
            filename = f"{conversation_id}.{format}"
            file_path = self.storage_path / filename

            if file_path.exists():
                file_path.unlink()
                logger.info(f"Recording deleted: {file_path}")
                return True
            else:
                logger.warning(f"Recording not found for deletion: {file_path}")
                return False

        except Exception as e:
            logger.error(f"Error deleting recording: {str(e)}")
            return False

    async def get_recording_info(
        self,
        conversation_id: UUID,
        format: str = "mp3",
    ) -> Optional[dict]:
        """
        Get metadata about a recording without loading it.

        Args:
            conversation_id: Conversation ID
            format: Audio format

        Returns:
            Dict with metadata or None if not found
        """
        try:
            filename = f"{conversation_id}.{format}"
            file_path = self.storage_path / filename

            if not file_path.exists():
                return None

            stat = file_path.stat()
            return {
                "file_path": str(file_path),
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "format": format,
            }

        except Exception as e:
            logger.error(f"Error getting recording info: {str(e)}")
            return None

    @staticmethod
    def convert_audio_format(
        audio_data: bytes,
        input_format: str,
        output_format: str,
    ) -> bytes:
        """
        Convert audio between formats.

        Args:
            audio_data: Audio bytes
            input_format: Input format (webm, mp3, wav)
            output_format: Output format

        Returns:
            Converted audio bytes
        """
        try:
            import ffmpeg

            # Use ffmpeg to convert
            # This would require ffmpeg to be installed
            logger.warning(
                f"Audio conversion not yet implemented: {input_format} → {output_format}"
            )
            return audio_data

        except ImportError:
            logger.warning("ffmpeg not available, returning original audio")
            return audio_data
        except Exception as e:
            logger.error(f"Error converting audio: {str(e)}")
            raise Exception(f"Audio conversion failed: {str(e)}") from e

    def cleanup_old_recordings(self, days: int = 30) -> int:
        """
        Delete recordings older than specified days.

        Args:
            days: Age threshold in days

        Returns:
            Number of files deleted
        """
        import time

        try:
            current_time = time.time()
            seconds_threshold = days * 24 * 60 * 60
            deleted_count = 0

            for file_path in self.storage_path.glob("*.*"):
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > seconds_threshold:
                        file_path.unlink()
                        deleted_count += 1
                        logger.info(f"Deleted old recording: {file_path}")

            logger.info(f"Cleanup complete: {deleted_count} files deleted")
            return deleted_count

        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            return 0
