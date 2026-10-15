"""Assemble the final 1080x1920 video with ffmpeg."""
import random
import subprocess
from pathlib import Path

from . import config

FONT = "DejaVu Sans"


def _run(args: list[str]) -> None:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def _ass_time(t: float) -> str:
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def _escape(text: str) -> str:
    return text.replace("\\", "").replace("{", "(").replace("}", ")")


def build_subtitles(segments: list[dict], hook_title: str, out: Path) -> None:
    """Big centred captions, 3 words at a time, plus the hook title for the first seconds."""
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {config.WIDTH}
PlayResY: {config.HEIGHT}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,{FONT},92,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,7,3,5,80,80,0,1
Style: Hook,{FONT},84,&H0000E5FF,&H0000E5FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,7,3,8,80,80,260,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [f"Dialogue: 1,{_ass_time(0)},{_ass_time(3.5)},Hook,,0,0,0,,{_escape(hook_title.upper())}"]
    t = 0.0
    for seg in segments:
        words = seg["text"].split()
        speech = max(seg["duration"] - 0.12, 0.5)  # 0.12 s pause padded in tts.py
        chunks = [words[i:i + 3] for i in range(0, len(words), 3)]
        total_chars = sum(len(" ".join(c)) for c in chunks) or 1
        start = t
        for chunk in chunks:
            text = " ".join(chunk)
            length = speech * len(text) / total_chars
            lines.append(
                f"Dialogue: 0,{_ass_time(start)},{_ass_time(start + length)},Caption,,0,0,0,,{_escape(text.upper())}"
            )
            start += length
        t += seg["duration"]
    out.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")


def normalise_clip(src: Path, out: Path, seconds: float) -> None:
    """Loop/trim the clip to `seconds`, crop to portrait, add a slow zoom for movement."""
    _run([
        "-stream_loop", "-1", "-i", str(src), "-t", f"{seconds:.3f}",
        "-vf",
        f"scale={config.WIDTH}:{config.HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={config.WIDTH}:{config.HEIGHT},fps={config.FPS},setsar=1,"
        f"scale=iw*1.06:ih*1.06,crop={config.WIDTH}:{config.HEIGHT}:"
        f"(iw-{config.WIDTH})*t/{seconds:.3f}:(ih-{config.HEIGHT})/2,"
        "eq=brightness=-0.06",
        "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
        str(out),
    ])


def assemble(segments: list[dict], hook_title: str, work: Path, out: Path) -> None:
    """segments: dicts with text, duration, audio (wav path) and clip (normalised mp4 path)."""
    video_list = work / "videos.txt"
    video_list.write_text("".join(f"file '{c.resolve()}'\n" for s in segments for c in s["clips"]))
    audio_list = work / "audios.txt"
    audio_list.write_text("".join(f"file '{s['audio'].resolve()}'\n" for s in segments))

    _run(["-f", "concat", "-safe", "0", "-i", str(video_list), "-c", "copy", str(work / "video.mp4")])
    _run(["-f", "concat", "-safe", "0", "-i", str(audio_list), "-c:a", "pcm_s16le", str(work / "voice.wav")])

    subs = work / "subs.ass"
    build_subtitles(segments, hook_title, subs)

    music = sorted(config.MUSIC_DIR.glob("*.mp3"))
    inputs = ["-i", str(work / "video.mp4"), "-i", str(work / "voice.wav")]
    if music:
        inputs += ["-stream_loop", "-1", "-i", str(random.choice(music))]
        audio_filter = "[2:a]volume=0.12[m];[1:a][m]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5[a]"
    else:
        audio_filter = "[1:a]loudnorm=I=-14:TP=-1.5[a]"

    _run([
        *inputs,
        "-filter_complex", f"[0:v]ass={subs}[v];{audio_filter}",
        "-map", "[v]", "-map", "[a]", "-shortest",
        "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
        str(out),
    ])
