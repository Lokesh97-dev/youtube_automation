# Legal & Compliance Notes

Practical risk notes for running this channel. **This is not legal advice.**
For anything with money behind it — merchandise, a registered trademark, an
incorporated business — talk to an actual IP attorney.

---

## 1. You probably cannot copyright these videos

The US Copyright Office's [January 2025 report on AI
copyrightability](https://www.copyright.gov/ai/) concluded that human
authorship is required, and that **prompting alone — however detailed — is
not authorship**. Purely AI-generated output is not copyrightable.

What this means in practice:

- Anyone can legally re-upload your videos, and you have limited recourse.
- You cannot meaningfully use Content ID to claim your own content.
- If you ever register anything, you must disclose the AI-generated portions
  and claim only your own human contribution (e.g. editing, curation,
  arrangement, original written material you actually wrote).

This does not prevent monetisation. It just means you own far less than the
effort suggests. If ownership matters to you, increase genuine human
authorship: write or heavily rewrite scripts yourself, and keep records of
what you contributed.

## 2. Trademark — the mascot name

The mascot name is **Hoplin**, chosen after screening candidates against
YouTube channels and trademark databases. Names rejected during screening and
why:

| Candidate | Why rejected |
|---|---|
| Rhymo | Existing YouTube channel + a music brand at rhymomusic.com |
| Wimbly | Active kids' YouTube channel in this exact niche |
| Thistlepop | Jellycat plush **bunny** product — direct conflict |
| Bramblewick | Too close to *Brambly Hedge*, a well-known children's series |
| Quillo | Several active YouTube channels |
| Sproutle | Too close to PBS Kids' *Sprout* children's channel |

**A web search is not a trademark clearance search.** Before you build brand
equity, print merchandise, or file anything:

1. Search the [USPTO trademark database](https://tmsearch.uspto.gov/) for the
   name in the relevant classes (Class 41 for entertainment services, Class 9
   for downloadable media, Class 28 for toys).
2. Check the equivalent registry in your own country.
3. Consider a clearance search by an attorney if you're going commercial.

The name lives in one place — `config/character_bible.yaml`. Changing it there
propagates to every prompt, so a rename later is cheap.

## 3. The mascot design

Generative image models can reproduce characters from their training data.
Two safeguards are in place:

- `config/character_bible.yaml` includes an explicit negative constraint that
  the character must not resemble any existing copyrighted, trademarked, or
  well-known character. This is injected into **every** image prompt.
- The mascot reference image requires a one-time human approval step
  (`scripts/generate_mascot.py`). **This is the only human checkpoint in the
  pipeline.** Reject anything that looks familiar.

Spot-check generated scene images periodically. Drift is possible.

## 4. COPPA / "Made for Kids" — a legal obligation

Content directed at children under 13 **must** be marked "Made for Kids" on
upload. This is FTC-enforced with per-violation penalties; it is not a
preference setting.

Consequences you should expect and accept:
- No personalised ads (lower RPM than general-audience content)
- Comments disabled
- No notifications, no Save-to-playlist, reduced discovery surface

Every generated video ships with an `UPLOAD_CHECKLIST.txt` in its artifact
that restates this. Don't skip it.

## 5. YouTube's inauthentic / mass-produced content policy

YouTube demonetises channels producing repetitive, templated, mass-produced
content. A daily fully-automated channel is squarely in the risk zone. The
mitigations built in:

- 20 rotating theme categories (`config/topics.yaml`) so lesson *type* varies
  systematically rather than by LLM whim
- A 90-item history window fed to the model as explicit "do not repeat this"
- Fuzzy-match rejection of near-duplicate titles/premises before scripting

**Do not weaken these to save tokens.** They are the difference between a
varied catalogue and a demonetised one. If you start seeing similar stories,
add categories rather than raising the similarity threshold.

## 6. Third-party assets — the easiest thing to get wrong

`assets/music/` and `assets/fonts/` are currently empty. Before adding
anything:

- **"Royalty-free" is not "public domain" and is not "cleared for YouTube."**
  Many royalty-free libraries still trigger Content ID claims. Prefer sources
  with an explicit YouTube/monetisation licence and **keep the licence file
  and a receipt/download record** for every track.
- **Fonts have licences too.** Open Sans is Apache-2.0 — ship the
  `LICENSE` file alongside the font file if you distribute it.
- Never use a font, image, or track you cannot produce a licence for.

## 7. Provider terms

- **OpenAI**: output ownership is assigned to you under their terms, and
  commercial use is permitted — but their usage policies still apply.
- **Google Cloud TTS**: commercial use permitted. Check current terms before
  relying on the synthetic voice as a brand asset.
- **Anthropic**: commercial use permitted under the API terms.

Provider terms change. Re-read them before scaling up.

## 8. Records worth keeping

If a dispute ever arises, contemporaneous records matter:

- `docs/data/videos.json` — a dated, git-versioned record of every video
- Git history — proof of when each prompt/config existed
- Licences and receipts for every third-party asset
- Notes on your own human contributions to each video
