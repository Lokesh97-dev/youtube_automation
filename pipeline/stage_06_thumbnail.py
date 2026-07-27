"""Stage 6: generate a high-quality thumbnail image and composite the
video's title text onto it."""
import json
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont

from pipeline import image_client, character_bible
from pipeline.config import CONFIG_DIR

THUMB_SIZE = (1280, 720)


def _load_font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("assets/fonts/OpenSans-Bold.ttf", size)
    except OSError:
        return ImageFont.load_default(size=size)


def run(video_id: str, out_dir: Path) -> dict:
    topic = json.loads((out_dir / "topic.json").read_text(encoding="utf-8"))
    script = json.loads((out_dir / "script.json").read_text(encoding="utf-8"))
    video_cfg = yaml.safe_load((CONFIG_DIR / "video.yaml").read_text(encoding="utf-8"))

    thumb_dir = out_dir / "thumbnail"
    base_image_path = thumb_dir / "base.png"

    hero_visual = script["scenes"][0]["visual_description"]
    prompt = character_bible.build_image_prompt(
        f"Thumbnail-style hero shot for the story '{topic['title']}': {hero_visual}. "
        "Bold, expressive pose, bright and eye-catching, leaves clear empty space "
        "in the lower third for title text."
    )
    image_client.generate_image(
        prompt, base_image_path, size="1536x1024", quality=video_cfg["image_quality_thumbnail"]
    )

    img = Image.open(base_image_path).convert("RGB").resize(THUMB_SIZE)
    draw = ImageDraw.Draw(img)
    font = _load_font(72)
    title = topic["title"].upper()

    # Simple bottom text band with outline for legibility over any artwork.
    text_bbox = draw.textbbox((0, 0), title, font=font)
    text_w = text_bbox[2] - text_bbox[0]
    x = max((THUMB_SIZE[0] - text_w) // 2, 20)
    y = THUMB_SIZE[1] - 160
    outline_range = 4
    for dx in range(-outline_range, outline_range + 1, 2):
        for dy in range(-outline_range, outline_range + 1, 2):
            draw.text((x + dx, y + dy), title, font=font, fill="black")
    draw.text((x, y), title, font=font, fill="white")

    final_thumb_path = thumb_dir / "thumb.jpg"
    img.save(final_thumb_path, "JPEG", quality=90)

    return {"thumbnail_path": str(final_thumb_path)}
