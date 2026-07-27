# Hoplin's Rhyme Time — Automated Kids Channel Pipeline

Fully automated daily pipeline for a kids' YouTube channel of short, narrated
(spoken, not sung) rhyming stories for ages 3-6 — moral/educational themes
(sharing, counting, manners, colors, kindness...) told by a recurring mascot,
**Hoplin the bunny**. Each run picks a fresh, non-repeating story, generates
narration + illustrations, assembles a captioned video, and updates a status
dashboard. You review the output and upload it to YouTube yourself — this
pipeline does not touch the YouTube API.

> **Read [docs/COMPLIANCE.md](docs/COMPLIANCE.md) before publishing anything.**
> It covers COPPA/"Made for Kids" (a legal obligation), why AI-generated
> videos are largely not copyrightable, trademark screening for the mascot
> name, and YouTube's mass-produced content policy.

## How it works

1. **Topic** — Claude picks a themed, never-before-used story premise.
2. **Script** — Claude writes the scene-by-scene rhyming narration.
3. **TTS** — Google Cloud Text-to-Speech narrates each scene.
4. **Images** — OpenAI `gpt-image-1` illustrates each scene, using a fixed
   character description + an approved reference portrait so Hoplin looks the
   same every day.
5. **Video** — `ffmpeg` assembles Ken Burns pan/zoom clips, captions, an
   optional watermark, and the narration track into `final.mp4`.
6. **Thumbnail** — a dedicated hero image with the title composited on top.
7. **Package** — the preview thumbnail + status are committed to the
   dashboard; the video, thumbnail, description, tags, and an upload
   checklist are uploaded as a downloadable GitHub Actions artifact.

Status of every video lives in `docs/data/videos.json` and is rendered by
the static dashboard at `docs/index.html`.

## One-time setup

1. **Get API keys** and add them as repo secrets (**Settings → Secrets and
   variables → Actions**):
   - `ANTHROPIC_API_KEY` — https://console.anthropic.com
   - `GOOGLE_TTS_API_KEY` — enable the Text-to-Speech API in a Google Cloud
     project, then create an API key (APIs & Services → Credentials)
   - `OPENAI_API_KEY` — https://platform.openai.com

2. **Generate and approve the mascot reference image once.** This is the only
   human checkpoint in the pipeline and it propagates into every video, so
   review it properly (see [COMPLIANCE §3](docs/COMPLIANCE.md)). With
   `OPENAI_API_KEY` set locally (copy `.env.example` to `.env`):
   ```
   pip install -r requirements.txt
   python scripts/generate_mascot.py --count 4
   # review out/mascot_candidates/, then approve your favourite:
   python scripts/generate_mascot.py --approve out/mascot_candidates/candidate_02.png
   ```
   Commit the resulting `assets/branding/mascot_reference.png`.

3. *(Optional)* Add a watermark PNG at `assets/branding/watermark.png`. If
   absent, the watermark overlay is skipped — the render still succeeds.

4. *(Optional)* Add `assets/fonts/OpenSans-Bold.ttf` for nicer thumbnail
   text — otherwise a default font is used. Ship its licence file too.

5. Enable GitHub Pages: **Settings → Pages → Source: Deploy from a branch →
   Branch: main, folder: /docs**.

## Running

- **Via GitHub Actions**: Actions tab → "Daily Video Generation" → Run
  workflow (optionally set a specific `date`).
- **Locally**: fill in `.env`, then `python scripts/run_pipeline.py`.

The pipeline runs on `workflow_dispatch` only for now. **Review several
videos' quality before uncommenting the daily `cron`** in
[.github/workflows/daily-video.yml](.github/workflows/daily-video.yml).

On your first runs, try `use_reference_image` both ways in
`config/video.yaml`. Passing the mascot reference to the image API gives the
strongest consistency, but can make the model anchor on the reference's
composition instead of building the requested scene. Keep whichever looks
better.

## After uploading a video

Run the **"Mark Video Uploaded"** workflow with the video's date and the
YouTube URL. This updates the dashboard without hand-editing JSON.

## Cost

Roughly **$0.50–0.85 per video** → **~$15–25/month** at one video/day. Actual
per-video spend is measured (not estimated) from real token/character/image
counts and shown on the dashboard; rates live in
[pipeline/costs.py](pipeline/costs.py) and should be checked against provider
pricing periodically.

Keep scene images at `medium` quality in `config/video.yaml` — moving all of
them to `high` pushes the monthly cost past $45.

## Testing

```
pip install -r requirements.txt
pytest tests/ -q
```

Tests cover the pure logic (topic rotation and de-duplication, status store
transitions, ffmpeg command construction, cost arithmetic). They do not call
paid APIs.

## Roadmap

- **Phase 2**: turn on the daily cron, add licensed background music with
  ducking, word-level caption timing, an intro/outro bumper.
- **Phase 3**: mascot outfit variants, embedding-based duplicate detection,
  multi-thumbnail selection, parallelised image generation.
