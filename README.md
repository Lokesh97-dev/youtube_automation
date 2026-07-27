# Rhymo's Rhyme Time — Automated Kids Channel Pipeline

Fully automated daily pipeline for a kids' YouTube channel of short, narrated
(spoken, not sung) rhyming stories for ages 3-6 — moral/educational themes
(sharing, counting, manners, colors, kindness...) told by a recurring mascot,
**Rhymo the bunny**. Each run picks a fresh, non-repeating story, generates
narration + illustrations, assembles a captioned video, and updates a status
dashboard. You review the output and upload it to YouTube yourself — this
pipeline does not touch the YouTube API.

## How it works

1. **Topic** — Claude picks a themed, never-before-used story premise.
2. **Script** — Claude writes the scene-by-scene rhyming narration.
3. **TTS** — Google Cloud Text-to-Speech narrates each scene.
4. **Images** — OpenAI `gpt-image-1` illustrates each scene, using a fixed
   character description + a reference portrait so Rhymo looks the same
   every day.
5. **Video** — `ffmpeg` assembles Ken Burns pan/zoom clips, captions, a
   watermark, and the narration track into `final.mp4`.
6. **Thumbnail** — a dedicated hero image with the title composited on top.
7. **Package** — the small preview thumbnail + status get committed to the
   dashboard; the full video/thumbnail/description/tags are uploaded as a
   downloadable GitHub Actions artifact.

Status of every video lives in `docs/data/videos.json` and is rendered by
the static dashboard at `docs/index.html` (enable via **Settings → Pages →
Deploy from branch: main / docs**).

## One-time setup

1. **Get API keys** and add them as repo secrets (**Settings → Secrets and
   variables → Actions**):
   - `ANTHROPIC_API_KEY` — https://console.anthropic.com
   - `GOOGLE_TTS_API_KEY` — enable the Text-to-Speech API in a Google Cloud
     project, then create an API key (APIs & Services → Credentials)
   - `OPENAI_API_KEY` — https://platform.openai.com
2. **Generate and approve the mascot reference image once** — this is what
   keeps Rhymo visually consistent across every future video (until this
   file exists, image generation falls back to text-only prompts, which
   drift over time). With `OPENAI_API_KEY` set locally (e.g. in a `.env`
   file, see `.env.example`):
   ```
   python scripts/generate_mascot.py --count 4
   # review the candidates in out/mascot_candidates/, then:
   python scripts/generate_mascot.py --approve out/mascot_candidates/candidate_02.png
   ```
   Commit the resulting `assets/branding/mascot_reference.png`.
3. **Add a watermark image** at `assets/branding/watermark.png` (small PNG,
   transparent background).
4. *(Optional)* Add a caption font at `assets/fonts/OpenSans-Bold.ttf` for
   custom thumbnail text styling — otherwise a default font is used.
5. Enable GitHub Pages: **Settings → Pages → Source: Deploy from a branch →
   Branch: main, folder: /docs**.

## Running

- **Manually via GitHub Actions**: Actions tab → "Daily Video Generation" →
  Run workflow (optionally set a specific `date`).
- **Locally**: `pip install -r requirements.txt`, copy `.env.example` to
  `.env` and fill in keys, then `python scripts/run_pipeline.py`.

The pipeline runs on `workflow_dispatch` only for now — review a few videos'
quality before uncommenting the daily `cron` schedule in
`.github/workflows/daily-video.yml`.

## After uploading a video

Run the **"Mark Video Uploaded"** workflow (Actions tab) with the video's
date and the YouTube URL — this updates the dashboard without needing to
edit any files by hand.

## Cost

Roughly **$0.50–0.85 per video** (Claude + Google TTS + `gpt-image-1` at
medium quality) → **~$15–25/month** at one video/day. Keep scene images at
`medium` quality (see `config/video.yaml`) — bumping all of them to `high`
can push the monthly cost past $45.

## Notes on YouTube policy

- This content targets children and must be marked **Made for Kids** on
  upload, which disables personalized ads/comments.
- To avoid YouTube's repetitive/inauthentic-content policy, every video's
  premise is checked against recent history and rejected if too similar
  (see `pipeline/topics_bank.py`) — keep this enabled even as you tune
  other parts of the pipeline.

## Roadmap

- **Phase 2**: turn on the daily cron, add background music with ducking,
  word-level caption timing, an intro/outro bumper, per-video cost tracking
  on the dashboard.
- **Phase 3**: mascot outfit variants, embedding-based duplicate detection,
  multi-thumbnail selection, parallelized image generation.
