# Anleitung: Dein tägliches TikTok-Video

Jeden Morgen um 7 Uhr passiert automatisch Folgendes:

1. Das Programm schaut, was in Deutschland gerade gesucht wird (Google Trends).
2. Claude wählt ein Thema, das zu deinem Kanal passt, und recherchiert Fakten im Internet.
3. Claude schreibt daraus einen Sprechertext für ein Video über 1 Minute.
4. Eine KI-Stimme liest den Text vor.
5. Passende kostenlose Videoclips werden von Pexels geladen, dazu große Untertitel.
6. Das fertige Video landet als **Entwurf in deiner TikTok-App**. Du schaust drüber und postest es.

Du musst einmal etwa 1 bis 2 Stunden einrichten. Danach brauchst du nur noch 2 Minuten am Tag.

**Kosten:** etwa 5 bis 10 € im Monat (Claude ca. 3 bis 8 €, Stimme ca. 1 €, alles andere gratis).

---

## Teil 1: GitHub (dort läuft das Programm, gratis)

1. Geh auf **github.com** und erstelle ein kostenloses Konto.
2. Oben rechts auf **+** und dann **New repository** tippen.
   - Name: `tiktok-pipeline`
   - **Public** auswählen (nötig für die kostenlose Webseite, die TikTok verlangt. Deine Schlüssel bleiben trotzdem geheim.)
   - **Create repository** tippen.
3. Dateien hochladen. Am einfachsten: Verbinde GitHub hier im Projekt mit Claude, dann lade ich alles für dich hoch.
   Selbst machen geht so: Entpacke `tiktok-pipeline.zip`, tippe in deinem Repo auf **uploading an existing file** und zieh **alle** Dateien und Ordner hinein, auch den Ordner `.github`. Dann **Commit changes**.
   (Auf dem Mac ist `.github` versteckt. Im Finder mit **Cmd + Shift + Punkt** sichtbar machen.)

## Teil 2: Drei Schlüssel besorgen

Ein Schlüssel ist wie ein Passwort, mit dem das Programm einen Dienst benutzen darf. Gib ihn niemandem.

| Dienst | Wo | Was tun |
|---|---|---|
| **Claude** (schreibt die Texte) | console.anthropic.com | Konto anlegen, unter **Billing** 10 $ aufladen, unter **API Keys** einen Schlüssel erstellen |
| **OpenAI** (Stimme) | platform.openai.com | Konto anlegen, unter **Billing** 5 $ aufladen, unter **API keys** einen Schlüssel erstellen |
| **Pexels** (Videoclips) | pexels.com/api | Kostenlos registrieren, Schlüssel wird sofort angezeigt |

Tipp: Stell bei Anthropic und OpenAI ein monatliches Limit ein (z. B. 15 $), dann kann nie mehr abgebucht werden.

## Teil 3: Schlüssel in GitHub eintragen

In deinem Repo: **Settings > Secrets and variables > Actions**

Unter **Secrets** jeweils **New repository secret**:

| Name | Wert |
|---|---|
| `ANTHROPIC_API_KEY` | Claude-Schlüssel |
| `OPENAI_API_KEY` | OpenAI-Schlüssel |
| `PEXELS_API_KEY` | Pexels-Schlüssel |

Dann oben auf den Reiter **Variables** und **New repository variable**:

| Name | Wert (Beispiel) |
|---|---|
| `NICHE` | `Technik, KI und Internet` (oder dein Thema, z. B. `Geld sparen und Finanzen`) |

## Teil 4: Erstes Testvideo

1. Im Repo oben auf **Actions** tippen. Falls gefragt: **I understand my workflows, go ahead and enable them**.
2. Links **Tägliches TikTok-Video** wählen, rechts **Run workflow** und nochmal **Run workflow**.
3. Nach etwa 5 bis 10 Minuten ist der Lauf grün. Klick drauf, ganz unten unter **Artifacts** liegt das Video (ZIP mit MP4 und Text).
4. Schau dir das Video an. Gefällt es dir, kannst du es schon jetzt von Hand bei TikTok hochladen. In der Textdatei stehen Beschreibung und Hashtags.

Ab jetzt entsteht jeden Tag um 7 Uhr automatisch ein neues Video. Auch ohne Teil 5 findest du es jeden Tag unter **Actions**.

## Teil 5: Automatisch in deine TikTok-App senden

### 5a. Webseite einschalten (TikTok verlangt Datenschutz-Seiten)
1. Öffne im Repo die Dateien `docs/privacy.html` und `docs/terms.html`, tippe auf den Stift und ersetze `[DEIN NAME]`, `[DEINE ADRESSE]`, `[DEINE E-MAIL]`. Speichern mit **Commit changes**.
2. **Settings > Pages**: bei **Branch** `main` und Ordner `/docs` wählen, **Save**.
3. Nach 1 bis 2 Minuten ist deine Seite online: `https://DEINNAME.github.io/tiktok-pipeline/`
   (DEINNAME = dein GitHub-Name in Kleinbuchstaben)

### 5b. TikTok-Entwickler-App anlegen
1. Geh auf **developers.tiktok.com**, melde dich mit deinem TikTok-Konto an.
2. **Manage apps > Connect an app**. Ausfüllen:
   - App-Name, Icon (irgendein Bild 1024x1024), kurze Beschreibung: „Private tool that uploads my own videos as drafts to my TikTok account.“
   - **Terms of Service URL:** `https://DEINNAME.github.io/tiktok-pipeline/terms.html`
   - **Privacy Policy URL:** `https://DEINNAME.github.io/tiktok-pipeline/privacy.html`
   - **Platform:** Web, Website: `https://DEINNAME.github.io/tiktok-pipeline/`
3. **Add products:** **Login Kit** und **Content Posting API** hinzufügen.
   - Bei Login Kit als **Redirect URI** eintragen: `https://DEINNAME.github.io/tiktok-pipeline/callback.html`
   - Bei Content Posting API **Direct Post NICHT** einschalten (brauchen wir nicht).
4. **Scopes:** `user.info.basic` und `video.upload`.
5. Zum Testen oben auf **Sandbox** wechseln, eine Sandbox anlegen, die gleichen Einstellungen übernehmen und unter **Target users** dein TikTok-Konto hinzufügen. Klappt der Upload im Sandbox-Modus nicht, reiche die App über **Submit for review** ein. Die Prüfung dauert meist ein paar Tage.
6. Notiere dir **Client Key** und **Client Secret**.

### 5c. Schlüssel eintragen
In GitHub unter **Settings > Secrets and variables > Actions > Secrets**:

| Name | Wert |
|---|---|
| `TIKTOK_CLIENT_KEY` | Client Key |
| `TIKTOK_CLIENT_SECRET` | Client Secret |
| `GH_PAT` | GitHub-Token, siehe unten |

**GH_PAT erstellen:** github.com > dein Profilbild > **Settings > Developer settings > Personal access tokens > Fine-grained tokens > Generate new token**. Bei **Repository access** nur `tiktok-pipeline` wählen, bei **Permissions** „Secrets: Read and write“. Ablauf auf 1 Jahr setzen. Damit darf das Programm deinen TikTok-Zugang selbst speichern und erneuern.

### 5d. TikTok verbinden
1. Öffne `https://DEINNAME.github.io/tiktok-pipeline/connect.html`
2. Client Key eintragen, **Bei TikTok anmelden**, Zugriff erlauben.
3. Du landest auf einer Seite mit einem langen Code. Kopieren.
4. In GitHub: **Actions > TikTok verbinden > Run workflow**, Code einfügen, starten. (Der Code gilt nur ein paar Minuten.)
5. Wird der Lauf grün, ist alles fertig.

## Teil 6: Jeden Tag (2 Minuten)

1. TikTok schickt dir eine Benachrichtigung, dass ein Video bereitliegt.
2. Öffne es, schau es an. Passt etwas nicht, lösch es einfach.
3. Beschreibung und Hashtags aus der Textdatei einfügen (unter **Actions** im Artifact), oder selbst schreiben.
4. **Wichtig:** Unter **Weitere Optionen** den Schalter **KI-generierte Inhalte** einschalten. TikTok verlangt das.
5. Posten.

---

## Regeln, damit dein Konto sicher bleibt und Geld verdienen kann

- Immer **KI-Kennzeichnung** einschalten.
- Kein fremdes Material (keine Filmszenen, keine fremden TikToks, keine Charts-Musik). Die Pexels-Clips sind erlaubt.
- Lieber 1 gutes Video am Tag als 5 schlechte. Massen-Content wird von TikTok aussortiert.
- Antworte auf Kommentare. Das zählt für den Algorithmus und zeigt, dass ein Mensch dahintersteht.
- **Creator Rewards** (Geld von TikTok) gibt es ab 18 Jahren, 10.000 Followern und 100.000 Aufrufen in 30 Tagen, nur für Videos über 1 Minute. Bewerben unter **Profil > Menü > TikTok Studio > Monetarisierung**.
- Sobald du Geld verdienst: Einnahmen bei der Steuer angeben. Bei regelmäßigen Einnahmen ggf. ein Kleingewerbe anmelden (kostet ca. 20 bis 60 €).

## Einstellungen ändern

Unter **Settings > Secrets and variables > Actions > Variables**:

| Variable | Wirkung |
|---|---|
| `NICHE` | Thema deines Kanals |
| `TTS_PROVIDER` | `edge` = kostenlose Microsoft-Stimme statt OpenAI (inoffizieller Dienst, ohne Garantie, OpenAI-Schlüssel dann nicht nötig) |

Uhrzeit ändern: in `.github/workflows/daily.yml` die Zeile `cron: "0 5 * * *"` (05:00 UTC = 7 Uhr Sommerzeit, 6 Uhr Winterzeit).

Eigene Hintergrundmusik: MP3-Dateien in den Ordner `music/` legen. Nur Musik, die du nutzen darfst (z. B. aus der YouTube Audio Library oder Pixabay Music).

## Wenn etwas nicht klappt

Unter **Actions** den roten Lauf öffnen, Fehlermeldung kopieren und mir hier schicken.
