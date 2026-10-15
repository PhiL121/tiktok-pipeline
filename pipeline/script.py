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
    prompt = f"""You are researching the topic for a TikTok video on a {config.LANGUAGE}-language channel.
Channel niche: {config.NICHE}

Current Google Trends ({config.TRENDS_GEO}):
{trend_lines or "(no trends available)"}

Topics we already covered, do not repeat:
{chr(10).join("- " + t for t in recent_topics) or "(none yet)"}

Task:
1. Pick ONE topic that fits the niche and is current. If no Google trend fits the niche, use web search \
to find a news story from the niche from the last few days.
2. Avoid topics about death, disasters, crime, divisive politics, health/medical advice and private \
individuals. Nothing that could spread hate, fear or misinformation.
3. Use web search to research 6 to 10 interesting facts. Verify every date, number and name against at \
least two independent sources. If sources disagree or you are unsure, leave the fact out.

Reply with: the chosen topic on the first line, then the verified facts as bullet points, \
then the source URLs."""
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
    prompt = f"""Turn these research notes into a voice-over script for a TikTok video in {config.LANGUAGE}.
Channel niche: {config.NICHE}

Research:
{notes}

Rules:
- At least {min_words} and at most {min_words + 50} words in total, so the video runs longer than 1 minute.
- The first sentence is a strong hook that makes people curious (no clickbait lies).
- Then 5 to 7 facts, told casually like to a friend, with your own take ("what this means for you").
- Only use facts from the research. Do not invent anything; copy dates and numbers exactly.
- End with a question for the comments and "Follow for more".
- segments: one entry per sentence (short sentences, max 20 words). "search" is 2 to 3 English \
keywords for matching stock footage (e.g. "smartphone hand", "city night"). No brand names or people.
- hook_title: max 6 words, shown on screen at the start.
- caption: TikTok description, max 150 characters.
- hashtags: 4 to 6 fitting hashtags without #.
- sources: the source URLs from the research."""
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
