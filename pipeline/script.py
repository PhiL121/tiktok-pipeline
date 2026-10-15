"""Pick a topic and write the video script with Claude.

Step 1: Claude picks a trend that fits the channel niche and researches it with web search.
Step 2: Claude turns the research notes into a structured script (JSON).
"""
import json

import anthropic

from . import config

BETAS = ["server-side-fallback-2026-07-01"]

client = anthropic.Anthropic()


def _create(**kwargs):
    return client.beta.messages.create(
        model=config.CLAUDE_MODEL,
        betas=BETAS,
        fallbacks="default",
        thinking={"type": "adaptive"},
        **kwargs,
    )


def _text(response) -> str:
    return "".join(b.text for b in response.content if b.type == "text").strip()


def research_topic(trends: list[dict], recent_topics: list[str]) -> str:
    trend_lines = "\n".join(
        f"- {t['keyword']} ({t['traffic']} Suchen) | "
        + "; ".join(n["title"] for n in t["news"][:2])
        for t in trends
    )
    prompt = f"""Du recherchierst das Thema für ein TikTok-Video auf einem {config.LANGUAGE}sprachigen Kanal.
Nische des Kanals: {config.NICHE}

Aktuelle Google-Trends ({config.TRENDS_GEO}):
{trend_lines or "(keine Trends verfügbar)"}

Diese Themen hatten wir schon, nicht wiederholen:
{chr(10).join("- " + t for t in recent_topics) or "(noch keine)"}

Aufgabe:
1. Wähle EIN Thema, das zur Nische passt und gerade aktuell ist. Passt kein Google-Trend zur Nische, \
such per Websuche nach einer aktuellen Nachricht der letzten Tage aus der Nische.
2. Vermeide Themen über Tod, Unglücke, Verbrechen, Politik-Streit, Gesundheit/Medizin-Ratschläge und \
private Personen. Nichts, was Hass, Angst oder Falschinformation verbreiten könnte.
3. Recherchiere mit der Websuche 6 bis 10 interessante, überprüfte Fakten dazu.

Antworte mit: dem gewählten Thema in der ersten Zeile, danach den Fakten als Stichpunkte, \
danach die Quellen-URLs."""
    messages = [{"role": "user", "content": prompt}]
    tools = [{"type": "web_search_20260209", "name": "web_search", "max_uses": 6}]
    response = _create(
        max_tokens=16000,
        output_config={"effort": "medium"},
        tools=tools,
        messages=messages,
    )
    # Server tools can pause a long turn; continue until it finishes.
    while response.stop_reason == "pause_turn":
        messages = messages[:1] + [{"role": "assistant", "content": response.content}]
        response = _create(
            max_tokens=16000,
            output_config={"effort": "medium"},
            tools=tools,
            messages=messages,
        )
    if response.stop_reason == "refusal":
        raise RuntimeError("Claude hat die Recherche abgelehnt.")
    notes = _text(response)
    if not notes:
        raise RuntimeError("Recherche lieferte keinen Text.")
    return notes


SCRIPT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["topic", "hook_title", "caption", "hashtags", "segments", "sources"],
    "properties": {
        "topic": {"type": "string"},
        "hook_title": {"type": "string"},
        "caption": {"type": "string"},
        "hashtags": {"type": "array", "items": {"type": "string"}},
        "segments": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["text", "search"],
                "properties": {"text": {"type": "string"}, "search": {"type": "string"}},
            },
        },
        "sources": {"type": "array", "items": {"type": "string"}},
    },
}


def write_script(notes: str, min_words: int = 200) -> dict:
    prompt = f"""Schreib aus diesen Recherche-Notizen ein Sprecher-Skript für ein TikTok-Video auf {config.LANGUAGE}.
Kanal-Nische: {config.NICHE}

Recherche:
{notes}

Regeln:
- Insgesamt mindestens {min_words} und höchstens {min_words + 50} Wörter, damit das Video über 1 Minute lang ist.
- Der erste Satz ist ein starker Hook, der neugierig macht (keine Clickbait-Lüge).
- Danach 5 bis 7 Fakten, locker erzählt wie zu einem Freund, mit eigener Einordnung ("Was das für dich heißt").
- Nur Fakten aus der Recherche verwenden, nichts erfinden.
- Am Ende eine Frage an die Zuschauer für Kommentare und "Folg mir für mehr".
- segments: ein Eintrag pro Satz (kurze Sätze, max. 20 Wörter). "search" sind 2 bis 3 englische \
Suchbegriffe für passendes Stock-Video (z. B. "smartphone hand", "city night"). Keine Markennamen oder Personen.
- hook_title: max. 6 Wörter, wird oben im Video eingeblendet.
- caption: TikTok-Beschreibung, max. 150 Zeichen.
- hashtags: 4 bis 6 passende Hashtags ohne #.
- sources: die Quellen-URLs aus der Recherche."""
    response = _create(
        max_tokens=16000,
        output_config={
            "effort": "medium",
            "format": {"type": "json_schema", "schema": SCRIPT_SCHEMA},
        },
        messages=[{"role": "user", "content": prompt}],
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("Claude hat das Skript abgelehnt.")
    script = json.loads(_text(response))
    script["segments"] = [s for s in script["segments"] if s["text"].strip()]
    if len(script["segments"]) < 5:
        raise RuntimeError("Skript ist zu kurz.")
    return script
