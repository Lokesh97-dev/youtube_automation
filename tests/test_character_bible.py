from pipeline import character_bible


def test_image_prompt_includes_character_description():
    prompt = character_bible.build_image_prompt("sitting under a tree at sunset")
    bible = character_bible.load()
    assert bible["name"] in prompt
    assert "sitting under a tree at sunset" in prompt


def test_image_prompt_always_carries_the_ip_safety_constraint():
    """Generative image models can reproduce characters from training data.
    This constraint is a legal safeguard and must reach every single prompt —
    see docs/COMPLIANCE.md."""
    prompt = character_bible.build_image_prompt("anything at all").lower()
    assert "copyrighted" in prompt
    assert "trademarked" in prompt


def test_image_prompt_forbids_text_in_image():
    prompt = character_bible.build_image_prompt("a scene").lower()
    assert "no text" in prompt


def test_reference_image_path_is_none_when_not_yet_approved():
    """Until the human-approved reference exists the pipeline must degrade to
    text-only prompts rather than crashing."""
    path = character_bible.reference_image_path()
    assert path is None or path.exists()
