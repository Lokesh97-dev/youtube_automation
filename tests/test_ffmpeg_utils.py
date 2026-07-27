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
    "video_bitrate": "4M",
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


def test_build_concat_list_file_writes_quoted_absolute_paths(tmp_path):
    clips = [tmp_path / "clip_01.mp4", tmp_path / "clip_02.mp4"]
    list_path = tmp_path / "list.txt"
    ffmpeg_utils.build_concat_list_file(clips, list_path)
    content = list_path.read_text()
    assert "clip_01.mp4" in content
    assert "clip_02.mp4" in content
    assert content.count("file '") == 2


def test_build_video_concat_cmd_uses_concat_demuxer():
    cmd = ffmpeg_utils.build_video_concat_cmd(Path("list.txt"), Path("out.mp4"))
    assert "-f" in cmd and "concat" in cmd
    assert cmd[-1] == "out.mp4"


def test_build_audio_concat_cmd_joins_paths_with_pipe():
    cmd = ffmpeg_utils.build_audio_concat_cmd([Path("a.mp3"), Path("b.mp3")], Path("out.aac"))
    concat_arg = cmd[cmd.index("-i") + 1]
    assert concat_arg == "concat:a.mp3|b.mp3"


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
        Path("silent.mp4"), Path("audio.aac"), Path("cap.srt"), Path("wm.png"), Path("final.mp4"), VIDEO_CFG
    )
    assert "-map" in cmd
    assert "[vout]" in cmd
    assert "1:a" in cmd
    assert cmd[-1] == "final.mp4"
