"""Stage 4: generate one illustration per scene, using the character bible
+ mascot reference image for cross-day visual consistency."""
import json
from pathlib import Path

import yaml

from pipeline import character_bible, image_client
from pipeline.config import CONFIG_DIR


def run(video_id: str, out_dir: Path) -> dict:
    script = json.loads((out_dir / "script.json").read_text(encoding="utf-8"))
    video_cfg = yaml.safe_load((CONFIG_DIR / "video.yaml").read_text(encoding="utf-8"))
    images_dir = out_dir / "images"
    use_reference = video_cfg.get("use_reference_image", True)

    image_paths = []
    for i, scene in enumerate(script["scenes"], start=1):
        prompt = character_bible.build_image_prompt(scene["visual_description"])
        image_path = images_dir / f"scene_{i:02d}.png"
        image_client.generate_image(
            prompt,
            image_path,
            size=video_cfg["image_size"],
            quality=video_cfg["image_quality_scenes"],
            use_reference=use_reference,
            out_dir=out_dir,
        )
        image_paths.append(str(image_path))

    result = {"image_paths": image_paths}
    (images_dir / "manifest.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
