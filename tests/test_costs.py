from pipeline import costs


def test_total_is_zero_before_anything_is_recorded(tmp_path):
    assert costs.total_usd(tmp_path) == 0.0


def test_records_accumulate_across_calls(tmp_path):
    costs.record_llm(tmp_path, 1000, 500)
    costs.record_llm(tmp_path, 1000, 500)
    costs.record_tts(tmp_path, 2000)
    costs.record_image(tmp_path, "medium")
    costs.record_image(tmp_path, "medium")
    costs.record_image(tmp_path, "high")

    expected = (
        2000 / 1_000_000 * costs.RATES["claude_input_per_mtok"]
        + 1000 / 1_000_000 * costs.RATES["claude_output_per_mtok"]
        + 2000 / 1_000_000 * costs.RATES["tts_neural2_per_mchar"]
        + 2 * costs.RATES["image_medium"]
        + 1 * costs.RATES["image_high"]
    )
    assert costs.total_usd(tmp_path) == round(expected, 4)


def test_unknown_image_quality_falls_back_to_medium_rate(tmp_path):
    costs.record_image(tmp_path, "some-new-tier")
    assert costs.total_usd(tmp_path) == round(costs.RATES["image_medium"], 4)


def test_a_typical_video_lands_in_the_expected_budget_range(tmp_path):
    """Guards the ~$0.50-0.85/video assumption the monthly budget rests on."""
    costs.record_llm(tmp_path, 8000, 3000)
    costs.record_tts(tmp_path, 4000)
    for _ in range(10):
        costs.record_image(tmp_path, "medium")
    costs.record_image(tmp_path, "high")

    assert 0.30 <= costs.total_usd(tmp_path) <= 1.00
