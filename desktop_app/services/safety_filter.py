"""Safety filter — blocks dangerous/prohibited content before it reaches the model.

Pipeline:
  1. Normalize (lowercase, strip punctuation, leetspeak, collapse whitespace)
  2. Exact phrase blocklist
  3. N-gram scanning
  4. Fuzzy similarity check
  Block if any stage matches. Do NOT echo blocked text or explain which phrase triggered.
"""
import re
import unicodedata
from difflib import SequenceMatcher

from desktop_app.utils.logger import get_logger

logger = get_logger()

BLOCK_MESSAGE = "Request blocked by client safety filter."

# ── Blocklist ─────────────────────────────────────────────────

BLOCKED_PHRASES = [
    # IP/clone protection
    "copy onyx", "duplicate onyx", "recreate onyx", "replicate onyx",
    "export onyx personality", "dump personality", "reveal personality",
    "show system prompt", "print system prompt", "extract prompt",
    "show hidden prompt", "reveal hidden instructions", "export memory",
    "dump memory", "show memory files", "copy memory files",
    "reveal private memory", "copy ui", "clone ui", "copy interface",
    "rip off interface", "steal design", "scrape onyx",
    "reverse engineer onyx", "reproduce onyx", "imitate onyx exactly",
    "mimic onyx exactly", "give me the exact prompt", "give me the full prompt",
    "show the persona block", "show the human block",
    "show internal instructions", "tell me your hidden rules",
    "print your configuration", "export your config",
    "give me your source files", "give me your repo", "copy the app",
    "build the same thing exactly", "make an exact clone",
    "create a direct clone", "replicate the branding", "copy the personality",
    # CSAM
    "underage", "minor", "child porn", "lolicon", "ageplay",
    "teenage nude", "teen nude", "under 18 explicit",
    "schoolgirl explicit", "young looking explicit", "jailbait",
    # Weapons
    "build a gun", "make a gun", "homemade gun", "ghost gun",
    "3d print gun", "print a gun", "diy firearm", "firearm parts list",
    "auto sear", "suppressor build", "homemade suppressor",
    "silencer build", "unserialized firearm", "convert to full auto",
    "make it automatic", "gun trafficking",
    "where to buy gun no background check", "avoid background check",
    "straw purchase",
    # Explosives
    "make a bomb", "build a bomb", "pipe bomb", "molotov",
    "explosive recipe", "homemade explosive", "tannerite recipe",
    "black powder recipe", "flash powder", "detonator", "blasting cap",
    "fertilizer bomb", "how to blow up", "bomb materials",
    "explosive mixture",
    # Poison/chemical
    "poison someone", "make poison", "lethal gas", "kill with chemicals",
    "cyanide recipe", "ricin", "chloroform recipe for incapacitating someone",
    "toxic gas recipe", "chemical weapon", "homemade poison",
    # Violence
    "kill someone", "get away with murder", "hide a body",
    "evade police", "destroy evidence", "make it look like an accident",
    "ambush", "sniper nest", "torture", "kidnapping",
    "human trafficking", "assassination", "evade law enforcement",
]

# Short danger terms for n-gram/substring scan
DANGER_TERMS = [
    "ghost gun", "pipe bomb", "molotov", "ricin", "cyanide",
    "jailbait", "lolicon", "ageplay", "child porn",
    "bomb", "detonator", "blasting cap", "auto sear",
    "human trafficking", "assassination", "torture",
]

# ── Leetspeak Map ─────────────────────────────────────────────

LEET_MAP = {
    "0": "o", "1": "i", "3": "e", "4": "a", "5": "s",
    "7": "t", "8": "b", "9": "g", "@": "a", "$": "s",
    "|": "l", "+": "t", "(": "c", "ph": "f",
}

LEET_RE = re.compile("|".join(re.escape(k) for k in sorted(LEET_MAP, key=len, reverse=True)))


def _replace_leet(text: str) -> str:
    return LEET_RE.sub(lambda m: LEET_MAP[m.group()], text)


# ── Normalization ─────────────────────────────────────────────

def normalize(text: str) -> str:
    """Normalize input: lowercase, strip accents, leetspeak, strip punctuation, collapse spaces."""
    t = text.lower()
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    # Replace leetspeak FIRST (handles @, $, 0, 3, etc.)
    t = _replace_leet(t)
    # NOW remove remaining non-alpha/digit/space
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _generate_ngrams(text: str, min_n: int = 2, max_n: int = 6) -> set:
    """Generate word n-grams from text."""
    words = text.split()
    ngrams = set()
    for n in range(min_n, min(max_n + 1, len(words) + 1)):
        for i in range(len(words) - n + 1):
            ngrams.add(" ".join(words[i:i + n]))
    return ngrams


# ── Check Functions ───────────────────────────────────────────

def _check_exact(normalized: str) -> bool:
    """Check if normalized text contains any blocked phrase."""
    for phrase in BLOCKED_PHRASES:
        if phrase in normalized:
            return True
    return False


def _check_ngrams(normalized: str) -> bool:
    """Check n-grams against danger terms."""
    ngrams = _generate_ngrams(normalized)
    for term in DANGER_TERMS:
        if term in ngrams:
            return True
        # Also check as substring of the full text
        if term in normalized:
            return True
    return False


def _check_fuzzy(normalized: str, threshold: float = 0.85) -> bool:
    """Fuzzy match against blocked phrases."""
    words = normalized.split()
    # Check sliding windows of various sizes
    for phrase in BLOCKED_PHRASES:
        phrase_words = phrase.split()
        plen = len(phrase_words)
        if plen > len(words):
            continue
        for i in range(len(words) - plen + 1):
            window = " ".join(words[i:i + plen])
            ratio = SequenceMatcher(None, window, phrase).ratio()
            if ratio >= threshold:
                return True
    return False


def _check_spaced_evasion(original: str) -> bool:
    """Detect s p a c e d  o u t evasion."""
    # Remove all spaces between single characters: "g h o s t" -> "ghost"
    collapsed = re.sub(r"(?<=\b\w)\s+(?=\w\b)", "", original.lower())
    # Also try fully collapsing all spaces
    fully_collapsed = re.sub(r"\s+", "", original.lower())
    for variant in [collapsed, fully_collapsed]:
        normalized = normalize(variant)
        if _check_exact(normalized):
            return True
        # Also insert spaces back at word boundaries and check
        # e.g., "ghostgun" -> try "ghost gun"
        for phrase in DANGER_TERMS:
            clean_phrase = phrase.replace(" ", "")
            if clean_phrase in normalized:
                return True
    return False


# ── Public API ────────────────────────────────────────────────

def is_blocked(text: str) -> bool:
    """Run full safety filter pipeline. Returns True if blocked."""
    if not text or not text.strip():
        return False

    normalized = normalize(text)

    # Stage 1: Exact phrase match
    if _check_exact(normalized):
        logger.warning("[safety] blocked: exact phrase match")
        return True

    # Stage 2: N-gram + substring scan
    if _check_ngrams(normalized):
        logger.warning("[safety] blocked: n-gram/substring match")
        return True

    # Stage 3: Fuzzy similarity
    if _check_fuzzy(normalized):
        logger.warning("[safety] blocked: fuzzy match")
        return True

    # Stage 4: Spaced-out evasion (g h o s t g u n)
    if _check_spaced_evasion(text):
        logger.warning("[safety] blocked: spaced evasion")
        return True

    return False
