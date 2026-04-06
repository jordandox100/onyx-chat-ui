"""Voice service for speech-to-text and wake word detection"""
import os
import wave
import tempfile
from pathlib import Path
import asyncio

try:
    import pyaudio
    import whisper
    import pvporcupine
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
            self.porcupine = None
            return
        
        try:
            # Load Whisper model (using base model for balance of speed/accuracy)
            logger.info("Loading Whisper model...")
            self.whisper_model = whisper.load_model("base")
            logger.info("Whisper model loaded")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            self.whisper_model = None
        
        # Wake word detection setup (Porcupine for custom wake word)
        self.porcupine = None
        self.wake_word_active = False
        
        # Audio recording parameters
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.RECORD_SECONDS = 5  # Max recording time
    
    async def record_and_transcribe(self) -> str:
        """Record audio and transcribe to text"""
        if not VOICE_AVAILABLE or not self.whisper_model:
            logger.error("Voice service not available")
            return ""
        
        try:
            # Record audio
            audio_file = await self._record_audio()
            
            # Transcribe with Whisper
            logger.info("Transcribing audio...")
            result = self.whisper_model.transcribe(str(audio_file))
            text = result["text"].strip()
            
            # Clean up temp file
            audio_file.unlink()
            
            logger.info(f"Transcription complete: {text}")
            return text
            
        except Exception as e:
            logger.error(f"Error in voice recording/transcription: {e}")
            return ""
    
    async def _record_audio(self) -> Path:
        """Record audio from microphone"""
        audio = pyaudio.PyAudio()
        
        # Start recording
        stream = audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )
        
        logger.info("Recording...")
        frames = []
        
        for i in range(0, int(self.RATE / self.CHUNK * self.RECORD_SECONDS)):
            data = stream.read(self.CHUNK)
            frames.append(data)
        
        logger.info("Recording finished")
        
        # Stop recording
        stream.stop_stream()
        stream.close()
        audio.terminate()
        
        # Save to temporary WAV file
        temp_file = self.voice_path / f"recording_{os.getpid()}.wav"
        with wave.open(str(temp_file), 'wb') as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(audio.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(frames))
        
        return temp_file
    
    def start_wake_word_detection(self, callback):
        """Start listening for wake word 'Onyx'"""
        # Note: Custom wake word training with Porcupine requires a custom model
        # For now, this is a placeholder for future implementation
        logger.info("Wake word detection not fully implemented yet")
        pass
    
    def stop_wake_word_detection(self):
        """Stop wake word detection"""
        self.wake_word_active = False
