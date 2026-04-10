"""Text-to-Speech service — Piper neural TTS with multiple voice models"""
import json
import wave
import io
import os
import subprocess
import threading
import tempfile
from pathlib import Path

from desktop_app.utils.logger import get_logger

logger = get_logger()

try:
    from piper import PiperVoice
    PIPER_AVAILABLE = True
except ImportError:
    PIPER_AVAILABLE = False
    logger.warning("piper-tts not installed. TTS disabled.")

VOICES_DIR = Path("Onyx/voices").absolute()

# Voice definitions: (display_name, model_file, speaker_id or None)
VOICE_OPTIONS = [
    ("Jarvis (British RP)",       "en_GB-alan-medium.onnx",                   None),
    ("British Male — Northern",   "en_GB-northern_english_male-medium.onnx",  None),
    ("British Male — Spike",      "en_GB-semaine-medium.onnx",                1),
    ("British Male — Obadiah",    "en_GB-semaine-medium.onnx",                2),
    ("American Male — Ryan",      "en_US-ryan-medium.onnx",                   None),
]


def _find_audio_player() -> str:
    """Find an available audio playback command."""
    for cmd in ["aplay", "paplay", "ffplay", "play"]:
        try:
            subprocess.run(["which", cmd], capture_output=True, check=True)
            return cmd
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    return ""


class TTSService:
    def __init__(self, config_path: Path = None):
        self._config_path = config_path or Path("Onyx/config").absolute()
        self._enabled = False
        self._voice_idx = 0
        self._speaking = False
        self._lock = threading.Lock()
        self._player = _find_audio_player()
        self._voice_cache: dict[str, PiperVoice] = {}

        self._load_settings()

        if not PIPER_AVAILABLE:
            logger.warning("Piper TTS not available.")
        elif not self._player:
            logger.warning("No audio player found (aplay/paplay/ffplay). TTS will generate but cannot play.")
        else:
            logger.info(f"TTS ready — player: {self._player}, voices: {len(self.available_voices)}")

    # ── Settings ──────────────────────────────────────────────

    def _load_settings(self):
        settings_file = self._config_path / "settings.json"
        if settings_file.exists():
            try:
                data = json.loads(settings_file.read_text())
                tts = data.get("tts", {})
                self._enabled = tts.get("enabled", False)
                self._voice_idx = tts.get("voice_idx", 0)
            except (json.JSONDecodeError, OSError):
                pass

    def _save_settings(self):
        settings_file = self._config_path / "settings.json"
        try:
            data = {}
            if settings_file.exists():
                data = json.loads(settings_file.read_text())
            data.setdefault("tts", {})
            data["tts"]["enabled"] = self._enabled
            data["tts"]["voice_idx"] = self._voice_idx
            settings_file.write_text(json.dumps(data, indent=2))
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to save TTS settings: {e}")

    # ── Properties ────────────────────────────────────────────

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
        return PIPER_AVAILABLE and bool(self.available_voices)

    @property
    def available_voices(self) -> list[tuple[str, str, int | None]]:
        """Return voices whose model files actually exist on disk."""
        result = []
        for name, model_file, speaker_id in VOICE_OPTIONS:
            if (VOICES_DIR / model_file).exists():
                result.append((name, model_file, speaker_id))
        return result

    @property
    def voice_index(self) -> int:
        return self._voice_idx

    @voice_index.setter
    def voice_index(self, idx: int):
        voices = self.available_voices
        if 0 <= idx < len(voices):
            self._voice_idx = idx
            self._save_settings()
            name = voices[idx][0]
            logger.info(f"TTS voice: {name}")

    # ── Synthesis + Playback ──────────────────────────────────

    def _load_voice(self, model_file: str) -> "PiperVoice | None":
        if model_file in self._voice_cache:
            return self._voice_cache[model_file]
        model_path = VOICES_DIR / model_file
        if not model_path.exists():
            logger.error(f"Voice model not found: {model_path}")
            return None
        try:
            voice = PiperVoice.load(str(model_path))
            self._voice_cache[model_file] = voice
            return voice
        except Exception as e:
            logger.error(f"Failed to load voice {model_file}: {e}")
            return None

    def speak(self, text: str):
        if not self._enabled or not PIPER_AVAILABLE:
            return
        t = threading.Thread(target=self._speak_sync, args=(text,), daemon=True)
        t.start()

    def _speak_sync(self, text: str):
        with self._lock:
            if self._speaking:
                return
            self._speaking = True
        try:
            voices = self.available_voices
            if not voices:
                return
            idx = min(self._voice_idx, len(voices) - 1)
            _, model_file, speaker_id = voices[idx]

            voice = self._load_voice(model_file)
            if not voice:
                return

            # Synthesize to a temp wav file
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp_path = tmp.name
            tmp.close()
            try:
                from piper.config import SynthesisConfig
                syn_config = SynthesisConfig(speaker_id=speaker_id)
                with wave.open(tmp_path, "wb") as wav_file:
                    voice.synthesize_wav(text, wav_file, syn_config=syn_config)

                # Play the wav
                if self._player == "ffplay":
                    subprocess.run(
                        [self._player, "-nodisp", "-autoexit", tmp.name],
                        capture_output=True, timeout=120,
                    )
                elif self._player == "paplay":
                    subprocess.run(
                        [self._player, tmp.name],
                        capture_output=True, timeout=120,
                    )
                else:
                    subprocess.run(
                        [self._player, tmp.name],
                        capture_output=True, timeout=120,
                    )
            finally:
                try:
                    os.unlink(tmp.name)
                except OSError:
                    pass
        except Exception as e:
            logger.error(f"TTS speak error: {e}")
        finally:
            with self._lock:
                self._speaking = False

    def stop(self):
        pass
