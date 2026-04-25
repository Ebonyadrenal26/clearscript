"""Tests for the VTT ingest adapter."""

from __future__ import annotations

from pathlib import Path

from clearscript.ingest import parse

SAMPLE_VTT = """WEBVTT

1
00:00:00.500 --> 00:00:03.000
<v Speaker 1>Hi everyone, can you hear me?</v>

2
00:00:03.000 --> 00:00:05.200
<v Speaker 2>Yes I can.</v>

3
00:00:05.200 --> 00:00:07.500
<v Speaker 1>Great, let's start.</v>
"""


def test_parses_vtt_voice_tags(tmp_path: Path) -> None:
    p = tmp_path / "sub.vtt"
    p.write_text(SAMPLE_VTT, encoding="utf-8")
    transcript = parse(p)
    speakers = [s.speaker_raw for s in transcript.segments]
    assert "Speaker 1" in speakers
    assert "Speaker 2" in speakers


def test_vtt_inline_speaker_fallback(tmp_path: Path) -> None:
    content = """WEBVTT

1
00:00:00.000 --> 00:00:02.000
Speaker 1: Hello there.

2
00:00:02.000 --> 00:00:04.000
Speaker 2: Hi.
"""
    p = tmp_path / "sub.vtt"
    p.write_text(content, encoding="utf-8")
    transcript = parse(p)
    speakers = [s.speaker_raw for s in transcript.segments]
    assert speakers == ["Speaker 1", "Speaker 2"]
