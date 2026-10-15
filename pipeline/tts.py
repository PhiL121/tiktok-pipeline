"""Text to speech, one audio file per sentence."""
import asyncio
import subprocess
from pathlib import Path

from . import config


def _openai_tts(text: str, out: Path) -> None:
    from openai import OpenAI

    client = OpenAI()
    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice=config.OPENAI_TTS_VOICE,
        input=text,
        instructions=f"Speak {config.LANGUAGE} like an energetic, natural TikTok creator talking to a friend. Upbeat, confident, quick pace, no announcer voice.",
        response_format="mp3",
    ) as resp:
        resp.stream_to_file(out)


def _edge_tts(text: str, out: Path) -> None:
    import edge_tts

    asyncio.run(edge_tts.Communicate(text, config.EDGE_TTS_VOICE, rate="+5%").save(str(out)))


def duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


def speak(text: str, out: Path) -> float:
    """Write speech for `text` to `out` (wav) and return its length in seconds."""
    raw = out.with_suffix(".mp3")
    if config.TTS_PROVIDER == "edge":
        _edge_tts(text, raw)
    else:
        _openai_tts(text, raw)
    # Normalise to wav with only a tiny pause: no dead air on TikTok.
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw),
         "-af", "apad=pad_dur=0.12", "-ar", "44100", "-ac", "2", str(out)],
        check=True,
    )
    return duration(out)
