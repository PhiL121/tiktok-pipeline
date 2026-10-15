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


def write_script(notes: str, min_words: int = 170) -> dict:
    prompt = f"""Turn these research notes into a voice-over script for a TikTok video in {config.LANGUAGE}.
Channel niche: {config.NICHE}

Research:
{notes}

Rules for a TikTok video that people watch to the end:
- Length: at least {min_words} and at most {min_words + 30} words in total (about 70 to 90 seconds).
- Hook (sentence 1, under 12 words): open with the most surprising fact, a bold claim or a direct \
"you" question. No greeting, no intro, no "In this video". It must be true, no clickbait lies.
- Sentence 2 opens a loop: promise a payoff that comes later (e.g. "but the last part is the craziest").
- Body: 4 to 6 facts, each in 1 to 2 short punchy sentences. Casual spoken language, like telling a friend. \
Use concrete numbers and comparisons people can picture.
- Re-hook every 15 to 20 seconds with a pattern interrupt ("But here's the thing.", "Wait, it gets better.").
- Give your own take on what it means for the viewer.
- Deliver the promised payoff near the end.
- Last sentence: one specific, easy question that invites comments (not "what do you think?"), \
then "Follow for more." Make the final line flow back into the hook so the video loops well.
- Only use facts from the research. Do not invent anything; copy dates and numbers exactly.
- segments: one entry per sentence (max 18 words). "search" is 2 to 3 concrete, visual English \
keywords for stock footage that matches what is being said (e.g. "stock market screen", "city night"). \
No brand names or people's names.
- hook_title: max 6 words, shown big on screen in the first seconds. Must make people stop scrolling.
- caption: TikTok description, max 150 characters. Start with the main search keywords people would type \
into TikTok search (TikTok is a search engine), then a short curiosity line.
- hashtags: 3 to 5 hashtags without #: 1 to 2 broad (e.g. "tech"), the rest specific to the topic. \
No "fyp" or "viral".
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
