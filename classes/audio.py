import os
import tempfile
import uuid
from io import BufferedIOBase
from typing import IO

from discord import FFmpegOpusAudio


class Audio(FFmpegOpusAudio):
    def __init__(
        self,
        source: str | BufferedIOBase,
        *,
        bitrate: int | None = None,
        codec: str | None = None,
        executable: str = "ffmpeg",
        pipe: bool = False,
        stderr: IO[bytes] | None = None,
        before_options: str | None = None,
        options: str | None = None,
    ) -> None:
        # Store logs in the OS temporary directory with a distinct prefix
        self._prefix = "discord_ffmpeg_"
        temp_dir = tempfile.gettempdir()
        self.log_filename = os.path.join(
            temp_dir, f"{self._prefix}{uuid.uuid4().hex}.log"
        )

        # Change level=32 to level=16 to filter out harmless network warnings
        os.environ["FFREPORT"] = f"file={self.log_filename}:level=16"

        super().__init__(
            source,
            bitrate=bitrate,
            codec=codec,
            executable=executable,
            pipe=pipe,
            stderr=stderr,
            before_options=before_options,
            options=options,
        )
        self.error_message: str | None = None
        self.__cleaned_up = False

    def read(self) -> bytes:
        ret = super().read()

        # FFmpeg stopped or crashed right here
        if not ret and self.error_message is None:
            self.__parse_log_file()

        return ret

    def kill(self) -> None:
        """Manually parse and destroy the log file when skipped via pause."""
        if not self.__cleaned_up:
            self.__parse_log_file()
            self.__safe_delete_log()
            self.__cleaned_up = True
            # Kill the underlying process so it doesn't become a zombie background task
            if self._process:
                try:
                    self._process.kill()
                except Exception:
                    pass

    def cleanup(self) -> None:
        """Handles final file deletions after 'after' has completely processed everything."""
        super().cleanup()
        if not self.__cleaned_up:
            self.__safe_delete_log()
            self.__cleaned_up = True

    def __parse_log_file(self) -> None:
        """Reads the independent log file while the audio player thread is still active."""
        if os.path.exists(self.log_filename):
            try:
                with open(
                    self.log_filename, "r", encoding="utf-8", errors="ignore"
                ) as f:
                    log_content = f.read()

                # Check for common FFmpeg error indicators
                if log_content and any(
                    x in log_content
                    for x in ("Error", "Server returned", "Invalid", "Failure")
                ):
                    self.error_message = log_content
            except Exception as e:
                print(f"Failed parsing log file during read loop: {e}")

    def __safe_delete_log(self) -> None:
        """Helper to delete the log file safely without raising errors."""
        if os.path.exists(self.log_filename):
            try:
                os.remove(self.log_filename)
            except OSError:
                pass

    def __del__(self) -> None:
        """
        Garbage Collection Fallback.
        Fires when the Audio object is deleted from memory (e.g., during a song skip).
        """
        self.__safe_delete_log()
