"""Upload a video to the TikTok inbox (drafts) via the official Content Posting API.

The video shows up as a notification in the TikTok app. You open it, add the caption,
switch on the "AI-generated content" label and post it yourself.
Docs: https://developers.tiktok.com/doc/content-posting-api-reference-upload-video
"""
import math
import os
import subprocess
import time
from pathlib import Path

import requests

from . import config

API = "https://open.tiktokapis.com/v2"
MIN_CHUNK = 5 * 1024 * 1024
MAX_CHUNK = 64 * 1024 * 1024


def refresh_access_token() -> str:
    resp = requests.post(
        f"{API}/oauth/token/",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_key": config.TIKTOK_CLIENT_KEY,
            "client_secret": config.TIKTOK_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": config.TIKTOK_REFRESH_TOKEN,
        },
        timeout=30,
    )
    data = resp.json()
    if "access_token" not in data:
        raise RuntimeError(f"TikTok-Token konnte nicht erneuert werden: {data}")
    new_refresh = data.get("refresh_token")
    if new_refresh and new_refresh != config.TIKTOK_REFRESH_TOKEN:
        _store_new_refresh_token(new_refresh)
    return data["access_token"]


def _store_new_refresh_token(token: str) -> None:
    """TikTok sometimes rotates the refresh token. Save it back as a GitHub secret if possible."""
    if os.environ.get("GH_TOKEN") and os.environ.get("GITHUB_REPOSITORY"):
        subprocess.run(
            ["gh", "secret", "set", "TIKTOK_REFRESH_TOKEN", "--repo", os.environ["GITHUB_REPOSITORY"]],
            input=token, text=True, check=True,
        )
        print("Neuer TikTok-Refresh-Token als Secret gespeichert.")
    else:
        print("WARNUNG: TikTok hat einen neuen Refresh-Token geschickt. Bitte GH_PAT-Secret anlegen oder TikTok neu verbinden.")


def _chunks(size: int) -> tuple[int, int]:
    if size <= MAX_CHUNK:
        return size, 1
    chunk = 10 * 1024 * 1024
    return chunk, math.floor(size / chunk)  # last chunk takes the remainder


def upload_to_inbox(video: Path) -> str:
    token = refresh_access_token()
    size = video.stat().st_size
    chunk_size, count = _chunks(size)
    resp = requests.post(
        f"{API}/post/publish/inbox/video/init/",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=UTF-8"},
        json={"source_info": {
            "source": "FILE_UPLOAD", "video_size": size,
            "chunk_size": chunk_size, "total_chunk_count": count,
        }},
        timeout=30,
    )
    body = resp.json()
    if body.get("error", {}).get("code") not in (None, "ok"):
        raise RuntimeError(f"TikTok-Upload-Start fehlgeschlagen: {body}")
    publish_id = body["data"]["publish_id"]
    upload_url = body["data"]["upload_url"]

    with open(video, "rb") as fh:
        for i in range(count):
            start = i * chunk_size
            end = size - 1 if i == count - 1 else start + chunk_size - 1
            fh.seek(start)
            data = fh.read(end - start + 1)
            r = requests.put(
                upload_url,
                headers={
                    "Content-Type": "video/mp4",
                    "Content-Length": str(len(data)),
                    "Content-Range": f"bytes {start}-{end}/{size}",
                },
                data=data,
                timeout=300,
            )
            if r.status_code not in (200, 201, 206):
                raise RuntimeError(f"TikTok-Upload Teil {i + 1} fehlgeschlagen: {r.status_code} {r.text}")

    for _ in range(20):
        time.sleep(6)
        status = requests.post(
            f"{API}/post/publish/status/fetch/",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=UTF-8"},
            json={"publish_id": publish_id},
            timeout=30,
        ).json()
        state = status.get("data", {}).get("status")
        print("TikTok-Status:", state)
        if state in ("SEND_TO_USER_INBOX", "PUBLISH_COMPLETE"):
            return publish_id
        if state == "FAILED":
            raise RuntimeError(f"TikTok hat das Video abgelehnt: {status}")
    return publish_id
