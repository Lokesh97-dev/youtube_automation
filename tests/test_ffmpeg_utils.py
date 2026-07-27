from pathlib import Path

from pipeline import ffmpeg_utils

VIDEO_CFG = {
    "fps": 30,
    "width": 1920,
    "height": 1080,
    "ken_burns_zoom_start": 1.0,
    "ken_burns_zoom_end": 1.08,
    "watermark_margin_px": 24,
    "caption_font_size": 46,
    "caption_margin_v": 80,
    "video_codec": "libx264",
    "crf": 20,
    "audio_codec": "aac",
}


def test_build_zoompan_cmd_includes_input_output_and_duration():
    cmd = ffmpeg_utils.build_zoompan_cmd(Path("scene_01.png"), Path("clip_01.mp4"), 5.0, VIDEO_CFG)
    assert cmd[0] == "ffmpeg"
    assert "scene_01.png" in cmd
    assert "clip_01.mp4" in cmd
    assert "5.000" in cmd
    assert any("zoompan" in part for part in cmd)


def test_build_zoompan_cmd_scales_to_double_target_resolution():
    cmd = ffmpeg_utils.build_zoompan_cmd(Path("s.png"), Path("c.mp4"), 3.0, VIDEO_CFG)
    filter_arg = cmd[cmd.index("-vf") + 1]
    assert "scale=3840:2160" in filter_arg
    assert "s=1920x1080" in filter_arg


def test_build_concat_list_file_writes_one_entry_per_clip(tmp_path):
    clips = [tmp_path / "clip_01.mp4", tmp_path / "clip_02.mp4"]
    list_path = tmp_path / "list.txt"
    ffmpeg_utils.build_concat_list_file(clips, list_path)
    content = list_path.read_text()
    assert "clip_01.mp4" in content
    assert "clip_02.mp4" in content
    assert content.count("file '") == 2


def test_build_concat_list_file_escapes_single_quotes(tmp_path):
    odd_dir = tmp_path / "it's a dir"
    odd_dir.mkdir()
    clip = odd_dir / "clip.mp4"
    list_path = tmp_path / "list.txt"
    ffmpeg_utils.build_concat_list_file([clip], list_path)
    # ffmpeg's concat syntax needs ' written as '\'' or the path terminates early.
    assert r"'\''" in list_path.read_text()


def test_build_video_concat_cmd_uses_concat_demuxer():
    cmd = ffmpeg_utils.build_video_concat_cmd(Path("list.txt"), Path("out.mp4"))
    assert "-f" in cmd and "concat" in cmd
    assert cmd[-1] == "out.mp4"


def test_build_audio_concat_cmd_uses_demuxer_not_concat_protocol():
    """The concat: protocol byte-joins MP3s (ID3 headers included) and drifts
    audio out of sync; the demuxer re-encodes to one correctly timed stream."""
    cmd = ffmpeg_utils.build_audio_concat_cmd(Path("list.txt"), Path("out.m4a"))
    assert "-f" in cmd and "concat" in cmd
    assert not any(part.startswith("concat:") for part in cmd)
    assert "aac" in cmd


def test_format_srt_timestamp():
    assert ffmpeg_utils.format_srt_timestamp(0) == "00:00:00,000"
    assert ffmpeg_utils.format_srt_timestamp(65.5) == "00:01:05,500"
    assert ffmpeg_utils.format_srt_timestamp(3661.25) == "01:01:01,250"


def test_build_srt_writes_sequential_blocks_with_correct_timing(tmp_path):
    out_path = tmp_path / "captions.srt"
    ffmpeg_utils.build_srt(["Hello there!", "Bye now!"], [2.0, 3.0], out_path)
    content = out_path.read_text()
    assert "1\n00:00:00,000 --> 00:00:02,000\nHello there!" in content
    assert "2\n00:00:02,000 --> 00:00:05,000\nBye now!" in content


def test_build_final_mux_cmd_maps_video_and_audio_streams():
    cmd = ffmpeg_utils.build_final_mux_cmd(
        Path("silent.mp4"), Path("audio.m4a"), Path("cap.srt"), Path("final.mp4"), VIDEO_CFG,
        watermark_path=Path("wm.png"),
    )
    assert "-map" in cmd
    assert "[vout]" in cmd
    assert "1:a" in cmd
    assert cmd[-1] == "final.mp4"


def test_build_final_mux_cmd_includes_watermark_overlay_when_provided():
    cmd = ffmpeg_utils.build_final_mux_cmd(
        Path("silent.mp4"), Path("audio.m4a"), Path("cap.srt"), Path("final.mp4"), VIDEO_CFG,
        watermark_path=Path("wm.png"),
    )
    filter_arg = cmd[cmd.index("-filter_complex") + 1]
    assert "overlay=" in filter_arg
    assert "wm.png" in cmd


def test_build_final_mux_cmd_omits_watermark_when_absent():
    """A missing branding asset must not stop a video rendering."""
    cmd = ffmpeg_utils.build_final_mux_cmd(
        Path("silent.mp4"), Path("audio.m4a"), Path("cap.srt"), Path("final.mp4"), VIDEO_CFG,
        watermark_path=None,
    )
    filter_arg = cmd[cmd.index("-filter_complex") + 1]
    assert "overlay=" not in filter_arg
    assert "[vout]" in filter_arg
    assert cmd.count("-i") == 2  # video + audio only


def test_build_final_mux_cmd_sets_crf_without_conflicting_bitrate():
    """CRF and a target bitrate together conflict; one is silently ignored."""
    cmd = ffmpeg_utils.build_final_mux_cmd(
        Path("silent.mp4"), Path("audio.m4a"), Path("cap.srt"), Path("final.mp4"), VIDEO_CFG,
    )
    assert "-crf" in cmd
    assert "-b:v" not in cmd
