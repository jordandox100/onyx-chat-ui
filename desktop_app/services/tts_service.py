"""Text-to-Speech service for ONYX"""
import json
import threading
from pathlib import Path
from desktop_app.utils.logger import get_logger

logger = get_logger()

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False


class TTSService:
    def __init__(self, config_path: Path = None):
        self._config_path = config_path or Path("Onyx/config").absolute()
        self._enabled = False
        self._engine = None
        self._rate = 175
        self._volume = 0.9
        self._voice_id = None
        self._speaking = False
        self._lock = threading.Lock()

        # Load saved settings
        self._load_settings()

        if TTS_AVAILABLE:
            try:
                self._engine = pyttsx3.init()
                self._engine.setProperty('rate', self._rate)
                self._engine.setProperty('volume', self._volume)
                self._pick_english_voice()
                logger.info("TTS service initialized")
            except Exception as e:
                logger.error(f"Failed to init TTS engine: {e}")
                self._engine = None
        else:
            logger.warning("pyttsx3 not installed. TTS disabled.")

    def _load_settings(self):
        """Load TTS settings from settings.json"""
        settings_file = self._config_path / "settings.json"
        if settings_file.exists():
            try:
                data = json.loads(settings_file.read_text())
                tts = data.get("tts", {})
                self._enabled = tts.get("enabled", False)
                self._rate = tts.get("rate", 175)
                self._volume = tts.get("volume", 0.9)
            except (json.JSONDecodeError, OSError):
                pass

    def _save_settings(self):
        """Persist current TTS settings back to settings.json"""
        settings_file = self._config_path / "settings.json"
        try:
            data = {}
            if settings_file.exists():
                data = json.loads(settings_file.read_text())
            data.setdefault("tts", {})
            data["tts"]["enabled"] = self._enabled
            data["tts"]["rate"] = self._rate
            data["tts"]["volume"] = self._volume
            settings_file.write_text(json.dumps(data, indent=2))
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to save TTS settings: {e}")

    def _pick_english_voice(self):
        if not self._engine:
            return
        voices = self._engine.getProperty('voices')
        for v in voices:
            name_lower = v.name.lower()
            if 'english' in name_lower and ('us' in name_lower or 'america' in name_lower):
                self._engine.setProperty('voice', v.id)
                self._voice_id = v.id
                logger.info(f"TTS voice: {v.name}")
                return
        for v in voices:
            if 'english' in v.name.lower():
                self._engine.setProperty('voice', v.id)
                self._voice_id = v.id
                logger.info(f"TTS voice (fallback): {v.name}")
                return

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value
        self._save_settings()
        logger.info(f"TTS {'enabled' if value else 'disabled'}")

    @property
    def available(self) -> bool:
        return TTS_AVAILABLE and self._engine is not None

    def speak(self, text: str):
        if not self._enabled or not self._engine:
            return
        t = threading.Thread(target=self._speak_sync, args=(text,), daemon=True)
        t.start()

    def _speak_sync(self, text: str):
        with self._lock:
            if self._speaking:
                return
            self._speaking = True
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', self._rate)
            engine.setProperty('volume', self._volume)
            if self._voice_id:
                engine.setProperty('voice', self._voice_id)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception as e:
            logger.error(f"TTS speak error: {e}")
        finally:
            with self._lock:
                self._speaking = False

    def stop(self):
        if self._engine:
            try:
                self._engine.stop()
            except Exception:
                pass

    def set_rate(self, rate: int):
        self._rate = rate
        if self._engine:
            self._engine.setProperty('rate', rate)
        self._save_settings()

    def set_volume(self, volume: float):
        self._volume = max(0.0, min(1.0, volume))
        if self._engine:
            self._engine.setProperty('volume', self._volume)
        self._save_settings()
