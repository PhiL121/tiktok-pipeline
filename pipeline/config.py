"""Settings, all read from environment variables (GitHub Secrets / Variables)."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK_DIR = ROOT / "work"
OUTPUT_DIR = ROOT / "output"
MUSIC_DIR = ROOT / "music"
HISTORY_FILE = ROOT / "data" / "history.json"

# "whatif" = a timeless "What if...?" science video every day; "trends" = current Google Trends topic
CONTENT_MODE = (os.environ.get("CONTENT_MODE") or "whatif")
# Channel topic, e.g. "Tech and AI", "History", "Money and saving"
NICHE = (os.environ.get("NICHE") or ("What if...? science scenarios" if CONTENT_MODE == "whatif" else "Tech, AI and the internet"))
LANGUAGE = (os.environ.get("LANGUAGE") or "English")
TRENDS_GEO = (os.environ.get("TRENDS_GEO") or "US")

CLAUDE_MODEL = (os.environ.get("CLAUDE_MODEL") or "claude-opus-5-5")

# "openai" (official, ~1 €/month) or "edge" (free, unofficial Microsoft Edge voice service)
TTS_PROVIDER = (os.environ.get("TTS_PROVIDER") or "openai")
OPENAI_TTS_VOICE = (os.environ.get("OPENAI_TTS_VOICE") or "ash")
EDGE_TTS_VOICE = (os.environ.get("EDGE_TTS_VOICE") or "en-US-AndrewMultilingualNeural")

PIXABAY_API_KEY = (os.environ.get("PIXABAY_API_KEY") or "")
PEXELS_API_KEY = (os.environ.get("PEXELS_API_KEY") or "")

TIKTOK_CLIENT_KEY = (os.environ.get("TIKTOK_CLIENT_KEY") or "").strip()
TIKTOK_CLIENT_SECRET = (os.environ.get("TIKTOK_CLIENT_SECRET") or "").strip()
TIKTOK_REFRESH_TOKEN = (os.environ.get("TIKTOK_REFRESH_TOKEN") or "")

MIN_SECONDS = 65  # Creator Rewards needs > 60 s; keep a safety margin
MAX_SECONDS = 95  # shorter videos keep a higher completion rate
MAX_SHOT_SECONDS = 2.8  # cut to a new clip at least this often
WIDTH, HEIGHT, FPS = 1080, 1920, 30
