"""Tests for ffmpeg command builder."""

from pathlib import Path
from worker.render import build_ffmpeg_command, _calc_center_crop


class TestCenterCrop:
    """Test center crop filter calculation."""

    def test_landscape_16_9(self):
        """Standard 16:9 source -> crop sides."""
        crop = _calc_center_crop(1920, 1080)
        assert "crop=607:1080:" in crop
        assert "scale=1080:1920" in crop

    def test_square(self):
        """Square source -> crop sides to 9:16 ratio."""
        crop = _calc_center_crop(1080, 1080)
        # 1080 * 0.5625 = 607 width, full 1080 height
        assert "crop=607:1080:" in crop
        assert "scale=1080:1920" in crop

    def test_already_vertical(self):
        """Already 9:16 -> minimal crop."""
        crop = _calc_center_crop(1080, 1920)
        assert "crop=1080:1920:0:0" in crop
        assert "scale=1080:1920" in crop


class TestBuildFfmpegCommand:
    """Test ffmpeg command construction."""

    def test_basic_command(self):
        cmd = build_ffmpeg_command(
            video_path=Path("/input.mp4"),
            output_path=Path("/output.mp4"),
            start=10.0,
            end=35.0,
            ass_path=None,
            src_width=1920,
            src_height=1080,
        )
        assert "ffmpeg" == cmd[0]
        assert "-y" in cmd
        assert "-ss" in cmd
        assert "10.0" in cmd
        assert "-t" in cmd
        assert "25.0" in cmd
        assert "-c:v" in cmd
        assert "libx264" in cmd
        assert "-c:a" in cmd
        assert "aac" in cmd
        assert "loudnorm" in cmd[cmd.index("-af") + 1]
        assert "-fs" in cmd
        assert str(Path("/output.mp4")) == cmd[-1]

    def test_includes_ass_subtitles(self, tmp_path):
        ass_file = tmp_path / "test.ass"
        ass_file.write_text("[Script Info]\nTitle: Test")

        cmd = build_ffmpeg_command(
            video_path=Path("/input.mp4"),
            output_path=Path("/output.mp4"),
            start=10.0,
            end=35.0,
            ass_path=ass_file,
            src_width=1920,
            src_height=1080,
        )
        vf = cmd[cmd.index("-vf") + 1]
        assert "subtitles=" in vf

    def test_no_ass_when_path_missing(self):
        cmd = build_ffmpeg_command(
            video_path=Path("/input.mp4"),
            output_path=Path("/output.mp4"),
            start=10.0,
            end=35.0,
            ass_path=Path("/nonexistent.ass"),
            src_width=1920,
            src_height=1080,
        )
        vf = cmd[cmd.index("-vf") + 1]
        assert "subtitles=" not in vf

    def test_duration_calculated(self):
        cmd = build_ffmpeg_command(
            video_path=Path("/input.mp4"),
            output_path=Path("/output.mp4"),
            start=100.5,
            end=130.5,
            ass_path=None,
            src_width=1920,
            src_height=1080,
        )
        t_idx = cmd.index("-t")
        assert cmd[t_idx + 1] == "30.0"
