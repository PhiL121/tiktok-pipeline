"""Download free stock clips from Pixabay or Pexels (both free for commercial use)."""
import random
import subprocess
from pathlib import Path

import requests

from . import config

API = "https://api.pexels.com/videos/search"
PIXABAY_API = "https://pixabay.com/api/videos/"


def _search_pixabay(query: str) -> list[dict]:
    """Return results in the same shape as Pexels: {id, video_files: [{link, height, file_type}]}."""
    resp = requests.get(
        PIXABAY_API,
        params={"key": config.PIXABAY_API_KEY, "q": query[:100], "per_page": 20, "safesearch": "true"},
        timeout=30,
    )
    resp.raise_for_status()
    results = []
    for hit in resp.json().get("hits", []):
        files = [
            {"link": v["url"], "height": v.get("height") or 0, "file_type": "video/mp4"}
            for v in hit.get("videos", {}).values()
            if v.get("url")
        ]
        results.append({"id": f"pixabay-{hit['id']}", "video_files": files})
    return results


def _search(query: str) -> list[dict]:
    if config.PIXABAY_API_KEY:
        return _search_pixabay(query)
    resp = requests.get(
        API,
        headers={"Authorization": config.PEXELS_API_KEY},
        params={"query": query, "orientation": "portrait", "per_page": 15, "size": "medium"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("videos", [])


def _best_file(video: dict) -> str | None:
    files = [
        f for f in video.get("video_files", [])
        if f.get("file_type") == "video/mp4" and (f.get("height") or 0) >= 720
    ]
    if not files:
        return None
    files.sort(key=lambda f: f.get("height") or 0)
    hd = [f for f in files if (f.get("height") or 0) >= 1080]
    return (hd or files)[0]["link"]  # smallest file that is still HD


def fetch_clip(query: str, out: Path, used_ids: set) -> bool:
    """Download one clip for `query`. Returns False if nothing usable was found."""
    if not (config.PIXABAY_API_KEY or config.PEXELS_API_KEY):
        return False
    for q in (query, " ".join(query.split()[:1]), "abstract background"):
        try:
            videos = [v for v in _search(q) if v["id"] not in used_ids]
        except requests.RequestException:
            continue
        random.shuffle(videos)
        for video in videos[:5]:
            link = _best_file(video)
            if not link:
                continue
            with requests.get(link, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(out, "wb") as fh:
                    for chunk in r.iter_content(1 << 20):
                        fh.write(chunk)
            used_ids.add(video["id"])
            return True
    return False


def placeholder_clip(out: Path, seconds: float, index: int) -> None:
    """Animated colour gradient, used when no stock clip is available."""
    colors = ["0x1e3a8a", "0x6d28d9", "0x0f766e", "0xb91c1c", "0xc2410c"]
    c = colors[index % len(colors)]
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
         "-i", f"gradients=s={config.WIDTH}x{config.HEIGHT}:c0={c}:c1=0x111111:speed=0.02:d={seconds:.2f}:r={config.FPS}",
         "-pix_fmt", "yuv420p", str(out)],
        check=True,
    )
