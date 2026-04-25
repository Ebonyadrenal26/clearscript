"""Tests for the SRT ingest adapter."""

from __future__ import annotations

from pathlib import Path

from clearscript.ingest import parse

SAMPLE_SRT = """1
00:00:00,500 --> 00:00:03,000
Speaker 1: Hi everyone, can you hear me?

2
00:00:03,000 --> 00:00:05,200
Speaker 2: Yes I can.

3
00:00:05,200 --> 00:00:07,500
Speaker 1: Great, let's start.

4
00:00:07,500 --> 00:00:10,000
And one more thing — welcome.
"""


def test_parses_srt(tmp_path: Path) -> None:
    p = tmp_path / "subs.srt"
    p.write_text(SAMPLE_SRT, encoding="utf-8")
    transcript = parse(p)

    # Speaker order: 1 (cue 1) → 2 (cue 2) → 1 (cues 3+4 merged)
    assert len(transcript.segments) == 3
    assert [s.speaker_raw for s in transcript.segments] == [
        "Speaker 1",
        "Speaker 2",
        "Speaker 1",
    ]
    assert transcript.segments[0].start_sec == 0.5
    assert transcript.duration_sec == 10.0
    # cue 4 has no leading speaker label and merges with the prior Speaker 1 turn
    assert "welcome" in transcript.segments[2].text.lower()


def test_srt_without_speaker_labels(tmp_path: Path) -> None:
    content = """1
00:00:00,000 --> 00:00:02,000
Hello there.

2
00:00:02,000 --> 00:00:04,000
General Kenobi.
"""
    p = tmp_path / "sub.srt"
    p.write_text(content, encoding="utf-8")
    transcript = parse(p)

    assert len(transcript.segments) == 1
    assert transcript.segments[0].speaker_raw is None
    assert "Hello there" in transcript.segments[0].text


def test_strips_styling_tags(tmp_path: Path) -> None:
    content = """1
00:00:00,000 --> 00:00:02,000
<i>Speaker 1</i>: <b>Hello</b>
"""
    p = tmp_path / "sub.srt"
    p.write_text(content, encoding="utf-8")
    transcript = parse(p)
    assert "Hello" in transcript.segments[0].text
    assert "<i>" not in transcript.to_markdown()
