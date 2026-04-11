"""Text-to-Speech — Piper neural TTS with speed control, naturalness, stop/restart"""
import json
import wave
import os
import subprocess
import threading
import tempfile
from pathlib import Path

from desktop_app.utils.logger import get_logger

logger = get_logger()

try:
    from piper import PiperVoice
    from piper.config import SynthesisConfig
    PIPER_AVAILABLE = True
except ImportError:
    PIPER_AVAILABLE = False
    SynthesisConfig = None
    logger.warning("piper-tts not installed. TTS disabled.")

VOICES_DIR = Path("Onyx/voices").absolute()

VOICE_OPTIONS = [
    ("Jarvis (British RP)",       "en_GB-alan-medium.onnx",                   None),
    ("British Male — Northern",   "en_GB-northern_english_male-medium.onnx",  None),
    ("British Male — Spike",      "en_GB-semaine-medium.onnx",                1),
    ("British Male — Obadiah",    "en_GB-semaine-medium.onnx",                2),
    ("American Male — Ryan",      "en_US-ryan-medium.onnx",                   None),
]

PREVIEW_TEXT = "Good evening sir. All systems are online and ready for your command."


def _find_audio_player() -> str:
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
        self._speed = 1.0
        self._speaking = False
        self._lock = threading.Lock()
        self._player = _find_audio_player()
        self._voice_cache: dict[str, PiperVoice] = {}
        self._current_process: subprocess.Popen | None = None
        self._last_text = ""
        self._stop_flag = threading.Event()

        self._load_settings()

        if not PIPER_AVAILABLE:
            logger.warning("Piper TTS not available.")
        elif not self._player:
            logger.warning("No audio player found (aplay/paplay/ffplay).")
        else:
            logger.info(f"TTS ready — player: {self._player}")

    # ── Settings ──────────────────────────────────────────────

    def _load_settings(self):
        settings_file = self._config_path / "settings.json"
        if settings_file.exists():
            try:
                data = json.loads(settings_file.read_text())
                tts = data.get("tts", {})
                self._enabled = tts.get("enabled", False)
                self._voice_idx = tts.get("voice_idx", 0)
                self._speed = tts.get("speed", 1.0)
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
            data["tts"]["speed"] = self._speed
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

    @property
    def is_speaking(self) -> bool:
        return self._speaking

    @property
    def available(self) -> bool:
        return PIPER_AVAILABLE and bool(self.available_voices)

    @property
    def available_voices(self) -> list[tuple[str, str, int | None]]:
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

    @property
    def speed(self) -> float:
        return self._speed

    @speed.setter
    def speed(self, val: float):
        self._speed = max(0.5, min(2.0, val))
        self._save_settings()

    # ── Voice loading ─────────────────────────────────────────

    def _load_voice(self, model_file: str) -> "PiperVoice | None":
        if model_file in self._voice_cache:
            return self._voice_cache[model_file]
        model_path = VOICES_DIR / model_file
        if not model_path.exists():
            return None
        try:
            voice = PiperVoice.load(str(model_path))
            self._voice_cache[model_file] = voice
            return voice
        except Exception as e:
            logger.error(f"Voice load error: {e}")
            return None

    def _make_synth_config(self, speaker_id=None) -> "SynthesisConfig":
        length_scale = 1.0 / self._speed if self._speed > 0 else 1.0
        return SynthesisConfig(
            speaker_id=speaker_id,
            length_scale=length_scale,
            noise_scale=0.8,
            noise_w_scale=0.9,
        )

    def _synthesize_to_file(self, text: str, voice_idx: int = None) -> str | None:
        voices = self.available_voices
        if not voices or not PIPER_AVAILABLE:
            return None
        idx = voice_idx if voice_idx is not None else min(self._voice_idx, len(voices) - 1)
        if idx < 0 or idx >= len(voices):
            return None
        _, model_file, speaker_id = voices[idx]
        voice = self._load_voice(model_file)
        if not voice:
            return None

        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp_path = tmp.name
        tmp.close()
        try:
            cfg = self._make_synth_config(speaker_id)
            with wave.open(tmp_path, "wb") as wf:
                voice.synthesize_wav(text, wf, syn_config=cfg)
            return tmp_path
        except Exception as e:
            logger.error(f"Synth error: {e}")
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            return None

    def _play_file(self, path: str):
        try:
            cmd = [self._player]
            if self._player == "ffplay":
                cmd += ["-nodisp", "-autoexit"]
            cmd.append(path)
            self._current_process = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            self._current_process.wait()
        except Exception as e:
            logger.error(f"Play error: {e}")
        finally:
            self._current_process = None
            try:
                os.unlink(path)
            except OSError:
                pass

    # ── Public API ────────────────────────────────────────────

    def speak(self, text: str):
        if not self._enabled or not PIPER_AVAILABLE or not self._player:
            return
        self._last_text = text
        self._stop_flag.clear()
        t = threading.Thread(target=self._speak_worker, args=(text, None), daemon=True)
        t.start()

    def preview(self, voice_idx: int):
        if not PIPER_AVAILABLE or not self._player:
            return
        self.stop()
        self._stop_flag.clear()
        t = threading.Thread(target=self._speak_worker, args=(PREVIEW_TEXT, voice_idx), daemon=True)
        t.start()

    def stop(self):
        self._stop_flag.set()
        proc = self._current_process
        if proc and proc.poll() is None:
            try:
                proc.kill()
            except OSError:
                pass
        with self._lock:
            self._speaking = False

    def restart(self):
        if self._last_text:
            self.stop()
            self._stop_flag.clear()
            t = threading.Thread(target=self._speak_worker, args=(self._last_text, None), daemon=True)
            t.start()

    def _speak_worker(self, text: str, voice_idx: int | None):
        with self._lock:
            if self._speaking:
                return
            self._speaking = True
        try:
            if self._stop_flag.is_set():
                return
            wav_path = self._synthesize_to_file(text, voice_idx)
            if not wav_path or self._stop_flag.is_set():
                if wav_path:
                    try:
                        os.unlink(wav_path)
                    except OSError:
                        pass
                return
            self._play_file(wav_path)
        except Exception as e:
            logger.error(f"TTS error: {e}")
        finally:
            with self._lock:
                self._speaking = False
