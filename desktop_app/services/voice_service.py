"""Voice service for speech-to-text using local Whisper"""
import os
import wave
import tempfile
from pathlib import Path

try:
    import pyaudio
    import whisper
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

from desktop_app.services.storage_service import StorageService
from desktop_app.utils.logger import get_logger

logger = get_logger()


class VoiceService:
    def __init__(self):
        """Initialize voice service with local Whisper"""
        self.storage = StorageService()
        self.voice_path = self.storage.voice_path

        if not VOICE_AVAILABLE:
            logger.warning("Voice libraries not available. Voice features disabled.")
            self.whisper_model = None
            return

        try:
            logger.info("Loading Whisper model...")
            self.whisper_model = whisper.load_model("base")
            logger.info("Whisper model loaded")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            self.whisper_model = None

        # Audio recording parameters
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.RECORD_SECONDS = 5

    async def record_and_transcribe(self) -> str:
        """Record audio and transcribe to text"""
        if not VOICE_AVAILABLE or not self.whisper_model:
            logger.error("Voice service not available")
            return ""

        try:
            audio_file = await self._record_audio()
            logger.info("Transcribing audio...")
            result = self.whisper_model.transcribe(str(audio_file))
            text = result["text"].strip()
            audio_file.unlink(missing_ok=True)
            logger.info(f"Transcription complete: {text}")
            return text

        except Exception as e:
            logger.error(f"Error in voice recording/transcription: {e}")
            return ""

    async def _record_audio(self) -> Path:
        """Record audio from microphone"""
        audio = pyaudio.PyAudio()

        stream = audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )

        logger.info("Recording...")
        frames = []

        for _ in range(0, int(self.RATE / self.CHUNK * self.RECORD_SECONDS)):
            data = stream.read(self.CHUNK)
            frames.append(data)

        logger.info("Recording finished")

        stream.stop_stream()
        stream.close()
        audio.terminate()

        temp_file = self.voice_path / f"recording_{os.getpid()}.wav"
        with wave.open(str(temp_file), 'wb') as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(audio.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(frames))

        return temp_file
