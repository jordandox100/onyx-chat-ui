"""Voice service — push-to-talk STT and wake word detection via local Whisper"""
import os
import wave
import time
from pathlib import Path

try:
    import pyaudio
    import whisper
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

from PySide6.QtCore import QThread, Signal

from desktop_app.services.storage_service import StorageService
from desktop_app.utils.logger import get_logger

logger = get_logger()


class VoiceService:
    def __init__(self):
        self.storage = StorageService()
        self.voice_path = self.storage.voice_path

        if not VOICE_AVAILABLE:
            logger.warning("Voice libs missing — voice features disabled.")
            self.whisper_model = None
            return

        try:
            logger.info("Loading Whisper model...")
            self.whisper_model = whisper.load_model("base")
            logger.info("Whisper model loaded")
        except Exception as e:
            logger.error(f"Whisper load failed: {e}")
            self.whisper_model = None

        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000

    async def record_and_transcribe(self, seconds: int = 5) -> str:
        if not VOICE_AVAILABLE or not self.whisper_model:
            return ""
        try:
            audio_file = await self._record_audio(seconds)
            result = self.whisper_model.transcribe(str(audio_file))
            text = result["text"].strip()
            audio_file.unlink(missing_ok=True)
            logger.info(f"Transcription: {text}")
            return text
        except Exception as e:
            logger.error(f"STT error: {e}")
            return ""

    async def _record_audio(self, seconds: int) -> Path:
        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=self.FORMAT, channels=self.CHANNELS,
            rate=self.RATE, input=True, frames_per_buffer=self.CHUNK,
        )
        frames = []
        for _ in range(int(self.RATE / self.CHUNK * seconds)):
            frames.append(stream.read(self.CHUNK))
        stream.stop_stream()
        stream.close()
        audio.terminate()

        out = self.voice_path / f"rec_{os.getpid()}.wav"
        with wave.open(str(out), "wb") as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(audio.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b"".join(frames))
        return out

    def transcribe_sync(self, seconds: int = 3) -> str:
        """Blocking transcription for wake-word detection thread."""
        if not VOICE_AVAILABLE or not self.whisper_model:
            return ""
        try:
            audio = pyaudio.PyAudio()
            stream = audio.open(
                format=self.FORMAT, channels=self.CHANNELS,
                rate=self.RATE, input=True, frames_per_buffer=self.CHUNK,
            )
            frames = []
            for _ in range(int(self.RATE / self.CHUNK * seconds)):
                frames.append(stream.read(self.CHUNK, exception_on_overflow=False))
            stream.stop_stream()
            stream.close()
            audio.terminate()

            tmp = self.voice_path / f"ww_{os.getpid()}.wav"
            with wave.open(str(tmp), "wb") as wf:
                wf.setnchannels(self.CHANNELS)
                wf.setsampwidth(audio.get_sample_size(self.FORMAT))
                wf.setframerate(self.RATE)
                wf.writeframes(b"".join(frames))

            result = self.whisper_model.transcribe(str(tmp))
            tmp.unlink(missing_ok=True)
            return result["text"].strip().lower()
        except Exception as e:
            logger.error(f"Wake-word listen error: {e}")
            return ""


class WakeWordThread(QThread):
    """Background thread that listens for the wake word 'onyx'."""
    wake_word_detected = Signal()

    def __init__(self, voice_service: VoiceService):
        super().__init__()
        self.voice_service = voice_service
        self._active = True

    def run(self):
        logger.info("Wake word listener started")
        while self._active:
            text = self.voice_service.transcribe_sync(seconds=2)
            if "onyx" in text:
                logger.info("Wake word detected!")
                self.wake_word_detected.emit()
                time.sleep(2)
            time.sleep(0.2)

    def stop(self):
        self._active = False
        self.wait(3000)
