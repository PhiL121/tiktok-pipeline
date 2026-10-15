# tiktok-pipeline

Erstellt jeden Tag automatisch ein TikTok-Video über 1 Minute zu einem aktuellen Trend und schickt es als Entwurf in die TikTok-App.

Einrichtung: siehe [ANLEITUNG.md](ANLEITUNG.md).

Ablauf: Google Trends → Claude (Recherche mit Websuche + Skript) → KI-Stimme → Pexels-Clips → ffmpeg (1080x1920, Untertitel) → TikTok Content Posting API (Upload to Inbox).
