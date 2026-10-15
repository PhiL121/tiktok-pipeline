"""Daily run: trend -> script -> voice -> clips -> video -> TikTok inbox."""
import json
import math
import shutil
from datetime import date
from pathlib import Path

from pipeline import config, media, render, script, trends, tts


def load_history() -> list[dict]:
    if config.HISTORY_FILE.exists():
        return json.loads(config.HISTORY_FILE.read_text(encoding="utf-8"))
    return []


def make_voice(segments: list[dict], work: Path) -> float:
    total = 0.0
    for i, seg in enumerate(segments):
        seg["audio"] = work / f"voice_{i:02d}.wav"
        seg["duration"] = tts.speak(seg["text"], seg["audio"])
        total += seg["duration"]
    return total


def make_clips(segments: list[dict], work: Path) -> None:
    """New clip every ~2.5 s: fast cuts keep viewers watching."""
    used: set = set()
    n = 0
    for i, seg in enumerate(segments):
        parts = max(1, math.ceil(seg["duration"] / config.MAX_SHOT_SECONDS))
        length = seg["duration"] / parts
        seg["clips"] = []
        for j in range(parts):
            raw = work / f"raw_{i:02d}_{j}.mp4"
            clip = work / f"clip_{i:02d}_{j}.mp4"
            if media.fetch_clip(seg["search"], raw, used):
                render.normalise_clip(raw, clip, length)
            else:
                media.placeholder_clip(clip, length, n)
            seg["clips"].append(clip)
            n += 1


def main() -> None:
    today = date.today().isoformat()
    shutil.rmtree(config.WORK_DIR, ignore_errors=True)
    config.WORK_DIR.mkdir(parents=True)
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    history = load_history()

    print("1/5 Trends holen ...")
    try:
        trend_list = trends.fetch_trends()
    except Exception as exc:  # the feed is unofficial; carry on with web search only
        print("Google Trends nicht erreichbar:", exc)
        trend_list = []

    print("2/5 Thema recherchieren und Skript schreiben ...")
    notes = script.research_topic(trend_list, [h["topic"] for h in history[-30:]])

    print("3/5 Stimme erzeugen ...")
    min_words = 170
    for _ in range(3):
        data = script.write_script(notes, min_words)
        segments = data["segments"]
        total = make_voice(segments, config.WORK_DIR)
        print(f"   Länge: {total:.1f} s")
        if config.MIN_SECONDS <= total <= config.MAX_SECONDS:
            break
        # Adjust the word count to the measured speaking speed and try again.
        target = (config.MIN_SECONDS + config.MAX_SECONDS) / 2
        min_words = max(120, int(min_words * target / total) - 15)
    else:
        if total < config.MIN_SECONDS:
            raise RuntimeError("Video wurde nicht länger als 1 Minute.")

    print("4/5 Clips laden und Video schneiden ...")
    make_clips(segments, config.WORK_DIR)
    video = config.OUTPUT_DIR / f"{today}.mp4"
    render.assemble(segments, data["hook_title"], config.WORK_DIR, video)

    caption = data["caption"] + "\n\n" + " ".join("#" + h.lstrip("#") for h in data["hashtags"])
    (config.OUTPUT_DIR / f"{today}.txt").write_text(
        f"{caption}\n\nThema: {data['topic']}\n\nSkript:\n"
        + "\n".join(s["text"] for s in segments)
        + "\n\nQuellen:\n" + "\n".join(data["sources"]) + "\n",
        encoding="utf-8",
    )
    print("   Fertig:", video, f"({total:.0f} s)")

    print("5/5 An TikTok senden ...")
    if config.TIKTOK_CLIENT_KEY and config.TIKTOK_REFRESH_TOKEN:
        from pipeline import tiktok

        tiktok.upload_to_inbox(video)
        print("   Video liegt jetzt als Entwurf in deiner TikTok-App.")
    else:
        print("   Kein TikTok-Zugang eingerichtet, Video nur als Download gespeichert.")

    history.append({"date": today, "topic": data["topic"], "seconds": round(total)})
    config.HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # Shows up as an annotation on the GitHub Actions run, readable without opening the log.
        import traceback

        tb = traceback.format_exc().strip().splitlines()
        print(f"::error title=Video fehlgeschlagen::{type(exc).__name__}: {exc} | " + " | ".join(tb[-6:]))
        raise
