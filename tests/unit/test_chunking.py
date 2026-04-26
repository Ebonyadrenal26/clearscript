"""Tests for the long-transcript chunker."""

from __future__ import annotations

from clearscript.core.chunking import (
    DEFAULT_TARGET_TOKENS,
    DEFAULT_TRIGGER_TOKENS,
    estimate_tokens,
    plan_chunks,
)
from clearscript.ingest.base import NormalizedTranscript, Segment


def _build(num_segments: int, chars_per_segment: int = 200) -> NormalizedTranscript:
    segments = []
    text_unit = "X" * chars_per_segment
    for i in range(num_segments):
        speaker = "Speaker 1" if i % 2 == 0 else "Speaker 2"
        segments.append(Segment(text=text_unit, speaker_raw=speaker))
    return NormalizedTranscript(
        segments=segments, source_format="test", detected_speakers=["Speaker 1", "Speaker 2"]
    )


def test_estimate_tokens_handles_ascii_and_cjk() -> None:
    assert estimate_tokens("hello world") > 0
    assert estimate_tokens("你好世界") > 0
    # CJK is denser per character (chars / 1.5) than ASCII (chars / 4)
    assert estimate_tokens("你好世界") > estimate_tokens("hello")


def test_short_transcript_stays_in_one_chunk() -> None:
    transcript = _build(num_segments=4, chars_per_segment=100)
    plan = plan_chunks(transcript)
    assert plan.num_chunks == 1
    assert plan.chunks[0] is transcript


def test_long_transcript_is_split_at_speaker_boundaries() -> None:
    # Build something well above the trigger threshold
    transcript = _build(num_segments=200, chars_per_segment=200)  # ~10k+ tokens
    plan = plan_chunks(transcript)
    assert plan.num_chunks > 1
    # No chunk should massively exceed target (allow 30% overshoot for boundary respect)
    for size in plan.estimated_tokens:
        assert size <= int(DEFAULT_TARGET_TOKENS * 1.3), f"chunk size {size} too big"
    # Total segments preserved
    total = sum(len(c.segments) for c in plan.chunks)
    assert total == 200


def test_oversized_single_segment_gets_split_internally() -> None:
    huge_text = "Long sentence ending. " * 1000  # ~5500 tokens in one segment
    transcript = NormalizedTranscript(
        segments=[Segment(text=huge_text, speaker_raw="Speaker 1")],
        source_format="test",
        detected_speakers=["Speaker 1"],
    )
    plan = plan_chunks(transcript, target_tokens=2000, trigger_tokens=500, hard_max_tokens=2000)
    assert plan.num_chunks > 1
    for size in plan.estimated_tokens:
        # Allow some overshoot from the sentence boundary respect
        assert size <= 2500


def test_empty_transcript_returns_single_empty_chunk() -> None:
    transcript = NormalizedTranscript(segments=[], source_format="test")
    plan = plan_chunks(transcript)
    assert plan.num_chunks == 1
    assert plan.chunks[0].segments == []


def test_chunk_preserves_source_format_and_speaker_metadata() -> None:
    transcript = _build(num_segments=80, chars_per_segment=250)
    plan = plan_chunks(transcript)
    for chunk in plan.chunks:
        assert chunk.source_format == "test"
        # detected_speakers should reflect what's actually in the chunk
        for seg in chunk.segments:
            if seg.speaker_raw:
                assert seg.speaker_raw in chunk.detected_speakers


def test_plan_total_tokens_accounting() -> None:
    transcript = _build(num_segments=100, chars_per_segment=200)
    plan = plan_chunks(transcript)
    assert plan.total_tokens > 0
    # Trigger threshold respected: total above means we chunked
    if plan.total_tokens > DEFAULT_TRIGGER_TOKENS:
        assert plan.num_chunks > 1
