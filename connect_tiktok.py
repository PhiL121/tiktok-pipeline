"""Exchange the TikTok login code for a refresh token and save it as a GitHub secret.

Runs in the "TikTok verbinden" workflow. Needs TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET,
TIKTOK_CODE, GH_TOKEN (GH_PAT secret) and GITHUB_REPOSITORY.
"""
import os
import subprocess
import urllib.parse

import requests

owner, repo = os.environ["GITHUB_REPOSITORY"].split("/")
redirect_uri = os.environ.get("TIKTOK_REDIRECT_URI") or f"https://{owner.lower()}.github.io/{repo}/callback.html"

resp = requests.post(
    "https://open.tiktokapis.com/v2/oauth/token/",
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    data={
        "client_key": os.environ["TIKTOK_CLIENT_KEY"],
        "client_secret": os.environ["TIKTOK_CLIENT_SECRET"],
        "code": urllib.parse.unquote(os.environ["TIKTOK_CODE"].strip()),
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    },
    timeout=30,
)
data = resp.json()
if "refresh_token" not in data:
    msg = f"{data.get('error')} {data.get('error_description')} (HTTP {resp.status_code})"
    print(f"::error title=TikTok-Fehler::{msg}")
    raise SystemExit(f"Fehler von TikTok: {msg}")
saved = subprocess.run(
    ["gh", "secret", "set", "TIKTOK_REFRESH_TOKEN", "--repo", os.environ["GITHUB_REPOSITORY"]],
    input=data["refresh_token"], text=True, capture_output=True,
)
if saved.returncode != 0:
    print(f"::error title=Secret speichern fehlgeschlagen (GH_PAT pruefen)::{saved.stderr.strip()}")
    raise SystemExit(1)
print(f"TikTok verbunden. Der Zugang gilt ca. {int(data.get('refresh_expires_in', 0)) // 86400} Tage.")
