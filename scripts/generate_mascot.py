#!/usr/bin/env python3
"""One-time setup helper: generate candidate portraits of the mascot so you
can pick one to become the permanent visual reference every future video is
anchored to.

REVIEW THIS CAREFULLY BEFORE APPROVING. This is the single human checkpoint
in an otherwise unattended pipeline. Reject any candidate that resembles a
character you recognise from an existing film, show, book, or game —
generative image models can reproduce characters from their training data,
and this one image propagates into every video you publish.

Usage:
    # 1. Generate a few candidates to review:
    python scripts/generate_mascot.py --count 4

    # 2. Look at out/mascot_candidates/*.png, then lock in your favorite:
    python scripts/generate_mascot.py --approve out/mascot_candidates/candidate_02.png
"""
import argparse
import base64
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from openai import OpenAI  # noqa: E402

from pipeline import character_bible  # noqa: E402
from pipeline.config import OPENAI_API_KEY, REPO_ROOT  # noqa: E402

CANDIDATES_DIR = REPO_ROOT / "out" / "mascot_candidates"
REFERENCE_PATH = REPO_ROOT / "assets" / "branding" / "mascot_reference.png"


def build_reference_prompt() -> str:
    bible = character_bible.load()
    return (
        f"{bible['style_prefix']}"
        f"Character reference sheet: {bible['description'].strip()} "
        "Full-body, front-facing, standing neutral pose, centered on a plain "
        "soft pastel background, no scene or props, no other characters. "
        f"{bible['style_suffix'].strip()} "
        f"Avoid: {'; '.join(bible['negative_constraints'])}."
    )


def generate(count: int) -> None:
    if not OPENAI_API_KEY:
        raise SystemExit("OPENAI_API_KEY is not set (set it in your environment or .env file).")

    client = OpenAI(api_key=OPENAI_API_KEY)
    prompt = build_reference_prompt()
    CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Prompt:\n{prompt}\n")
    for i in range(1, count + 1):
        print(f"Generating candidate {i}/{count}...")
        result = client.images.generate(model="gpt-image-1", prompt=prompt, size="1024x1024", quality="high")
        image_bytes = base64.b64decode(result.data[0].b64_json)
        out_path = CANDIDATES_DIR / f"candidate_{i:02d}.png"
        out_path.write_bytes(image_bytes)
        print(f"  saved {out_path}")

    print(
        f"\nReview the {count} candidates in {CANDIDATES_DIR}, then approve your favorite with:\n"
        f"  python scripts/generate_mascot.py --approve {CANDIDATES_DIR / 'candidate_01.png'}"
    )


def approve(candidate_path: Path) -> None:
    if not candidate_path.exists():
        raise SystemExit(f"{candidate_path} does not exist.")
    REFERENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(candidate_path, REFERENCE_PATH)
    name = character_bible.load()["name"]
    print(f"Approved. Saved as {REFERENCE_PATH} — commit this file to lock in {name}'s look.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=4, help="Number of candidate portraits to generate.")
    parser.add_argument("--approve", type=Path, default=None, help="Path to a candidate to lock in as the reference image.")
    args = parser.parse_args()

    if args.approve:
        approve(args.approve)
    else:
        generate(args.count)


if __name__ == "__main__":
    main()
