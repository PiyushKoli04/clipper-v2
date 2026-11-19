"""Tests for highlight JSON validator and extractor."""

import pytest
from worker.highlights import _extract_json, _validate_highlights
from worker.config import ClipperConfig


class TestExtractJson:
    """Test JSON extraction from LLM responses."""

    def test_clean_json(self):
        text = '[{"start": 10, "end": 35, "hook_title": "Test", "virality_score": 85}]'
        result = _extract_json(text)
        assert len(result) == 1
        assert result[0]["start"] == 10

    def test_markdown_fences(self):
        text = '```json\n[{"start": 10, "end": 35, "hook_title": "Test", "virality_score": 85}]\n```'
        result = _extract_json(text)
        assert len(result) == 1

    def test_embedded_in_text(self):
        text = 'Here are the clips:\n[{"start": 10, "end": 35, "hook_title": "Test", "virality_score": 85}]\nDone!'
        result = _extract_json(text)
        assert len(result) == 1

    def test_dict_with_clips_key(self):
        text = '{"clips": [{"start": 10, "end": 35, "hook_title": "Test", "virality_score": 85}]}'
        result = _extract_json(text)
        assert len(result) == 1

    def test_invalid_json_raises(self):
        with pytest.raises(ValueError):
            _extract_json("not json at all")


class TestValidateHighlights:
    """Test highlight validation and repair."""

    def setup_method(self):
        self.config = ClipperConfig(
            clips_per_video=3,
            min_clip_seconds=20,
            max_clip_seconds=45,
        )

    def test_valid_highlights(self):
        highlights = [
            {"start": 10, "end": 35, "hook_title": "Hook 1", "virality_score": 90, "reason": "Great"},
            {"start": 40, "end": 65, "hook_title": "Hook 2", "virality_score": 80, "reason": "Good"},
        ]
        result = _validate_highlights(highlights, self.config, 120.0)
        assert len(result) == 2
        assert result[0]["virality_score"] == 90  # sorted by score

    def test_too_short_skipped(self):
        highlights = [
            {"start": 10, "end": 20, "hook_title": "Short", "virality_score": 95, "reason": ""},
        ]
        result = _validate_highlights(highlights, self.config, 120.0)
        assert len(result) == 0

    def test_too_long_trimmed(self):
        highlights = [
            {"start": 10, "end": 70, "hook_title": "Long", "virality_score": 85, "reason": ""},
        ]
        result = _validate_highlights(highlights, self.config, 120.0)
        assert len(result) == 1
        assert result[0]["end"] == 10 + 45  # trimmed to max

    def test_overlapping_removed(self):
        highlights = [
            {"start": 10, "end": 40, "hook_title": "A", "virality_score": 90, "reason": ""},
            {"start": 30, "end": 55, "hook_title": "B", "virality_score": 80, "reason": ""},
        ]
        result = _validate_highlights(highlights, self.config, 120.0)
        assert len(result) == 1
        assert result[0]["hook_title"] == "A"

    def test_clamped_to_video_duration(self):
        highlights = [
            {"start": 100, "end": 130, "hook_title": "End", "virality_score": 70, "reason": ""},
        ]
        result = _validate_highlights(highlights, self.config, 110.0)
        # end clamped to 110, duration = 10 < 20 min, so skipped
        assert len(result) == 0

    def test_score_clamped(self):
        highlights = [
            {"start": 10, "end": 35, "hook_title": "Score", "virality_score": 150, "reason": ""},
        ]
        result = _validate_highlights(highlights, self.config, 120.0)
        assert result[0]["virality_score"] == 100

    def test_missing_fields_skipped(self):
        highlights = [
            {"start": 10, "hook_title": "Missing end"},
        ]
        result = _validate_highlights(highlights, self.config, 120.0)
        assert len(result) == 0

    def test_top_n_returned(self):
        highlights = [
            {"start": i * 50, "end": i * 50 + 25, "hook_title": f"H{i}", "virality_score": 50 + i * 10, "reason": ""}
            for i in range(5)
        ]
        result = _validate_highlights(highlights, self.config, 300.0)
        assert len(result) == 3  # clips_per_video = 3

