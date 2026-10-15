"""Settings, all read from environment variables (GitHub Secrets / Variables)."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK_DIR = ROOT / "work"
OUTPUT_DIR = ROOT / "output"
MUSIC_DIR = ROOT / "music"
HISTORY_FILE = ROOT / "data" / "history.json"

# Channel topic, e.g. "Technik und KI", "Geschichte", "Geld und Sparen"
NICHE = (os.environ.get("NICHE") or "Technik, KI und Internet")
LANGUAGE = (os.environ.get("LANGUAGE") or "Deutsch")
TRENDS_GEO = (os.environ.get("TRENDS_GEO") or "DE")

CLAUDE_MODEL = (os.environ.get("CLAUDE_MODEL") or "claude-opus-5-5")

# "openai" (official, ~1 €/month) or "edge" (free, unofficial Microsoft Edge voice service)
TTS_PROVIDER = (os.environ.get("TTS_PROVIDER") or "openai")
OPENAI_TTS_VOICE = (os.environ.get("OPENAI_TTS_VOICE") or "onyx")
EDGE_TTS_VOICE = (os.environ.get("EDGE_TTS_VOICE") or "de-DE-ConradNeural")

PIXABAY_API_KEY = (os.environ.get("PIXABAY_API_KEY") or "")
PEXELS_API_KEY = (os.environ.get("PEXELS_API_KEY") or "")

TIKTOK_CLIENT_KEY = (os.environ.get("TIKTOK_CLIENT_KEY") or "")
TIKTOK_CLIENT_SECRET = (os.environ.get("TIKTOK_CLIENT_SECRET") or "")
TIKTOK_REFRESH_TOKEN = (os.environ.get("TIKTOK_REFRESH_TOKEN") or "")

MIN_SECONDS = 65  # Creator Rewards needs > 60 s; keep a safety margin
WIDTH, HEIGHT, FPS = 1080, 1920, 30
