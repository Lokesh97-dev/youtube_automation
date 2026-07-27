"""Stage 6: generate a high-quality thumbnail image and composite the
video's title text onto it."""
import json
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont

from pipeline import character_bible, image_client
from pipeline.config import CONFIG_DIR, REPO_ROOT

THUMB_SIZE = (1280, 720)
TEXT_SIDE_MARGIN = 40
FONT_PATH = REPO_ROOT / "assets" / "fonts" / "OpenSans-Bold.ttf"


def _load_font(size: int) -> ImageFont.ImageFont:
    """Font path must be absolute — a relative path silently depended on the
    process's working directory."""
    try:
        return ImageFont.truetype(str(FONT_PATH), size)
    except OSError:
        return ImageFont.load_default(size=size)


def _wrap_title(draw: ImageDraw.ImageDraw, title: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    """Greedy word wrap. Without this, titles up to 70 chars ran straight off
    the edge of the thumbnail."""
    words = title.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=font) <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _fit_title(
    draw: ImageDraw.ImageDraw, title: str, max_width: int, start_size: int, max_lines: int
) -> tuple[ImageFont.ImageFont, list[str]]:
    """Shrink the font until the title fits within max_lines."""
    size = start_size
    while size >= 28:
        font = _load_font(size)
        lines = _wrap_title(draw, title, font, max_width)
        if len(lines) <= max_lines:
            return font, lines
        size -= 6
    font = _load_font(28)
    return font, _wrap_title(draw, title, font, max_width)[:max_lines]


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
        prompt,
        base_image_path,
        size=video_cfg["image_size"],
        quality=video_cfg["image_quality_thumbnail"],
        use_reference=video_cfg.get("use_reference_image", True),
        out_dir=out_dir,
    )

    img = Image.open(base_image_path).convert("RGB").resize(THUMB_SIZE)
    draw = ImageDraw.Draw(img)

    title = topic["title"].upper()
    max_text_width = THUMB_SIZE[0] - (TEXT_SIDE_MARGIN * 2)
    font, lines = _fit_title(
        draw,
        title,
        max_text_width,
        video_cfg.get("thumbnail_font_size", 72),
        video_cfg.get("thumbnail_max_title_lines", 3),
    )

    line_height = int(font.size * 1.15)
    block_height = line_height * len(lines)
    y = THUMB_SIZE[1] - block_height - 48
    outline_range = 4

    for line in lines:
        line_width = draw.textlength(line, font=font)
        x = (THUMB_SIZE[0] - line_width) / 2
        for dx in range(-outline_range, outline_range + 1, 2):
            for dy in range(-outline_range, outline_range + 1, 2):
                draw.text((x + dx, y + dy), line, font=font, fill="black")
        draw.text((x, y), line, font=font, fill="white")
        y += line_height

    final_thumb_path = thumb_dir / "thumb.jpg"
    img.save(final_thumb_path, "JPEG", quality=90)

    return {"thumbnail_path": str(final_thumb_path)}
