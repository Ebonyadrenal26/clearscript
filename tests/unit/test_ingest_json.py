"""Tests for the JSON ingest adapter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from clearscript.ingest import parse


def write(tmp_path: Path, payload, name: str = "t.json") -> Path:
    p = tmp_path / name
    p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return p


def test_whisper_segments_shape(tmp_path: Path) -> None:
    payload = {
        "text": "full transcript",
        "segments": [
            {"text": "Hi everyone.", "start": 0.0, "end": 1.5, "speaker": "SPEAKER_00"},
            {"text": "Hello.", "start": 1.5, "end": 2.5, "speaker": "SPEAKER_01"},
        ],
    }
    transcript = parse(write(tmp_path, payload))
    assert len(transcript.segments) == 2
    assert transcript.segments[0].speaker_raw == "SPEAKER_00"
    assert transcript.segments[0].start_sec == 0.0
    assert transcript.duration_sec == 2.5


def test_plaud_shape(tmp_path: Path) -> None:
    payload = {
        "transcripts": [
            {"speaker": "Host", "text": "Welcome.", "begin": 0.5, "end": 1.5},
            {"speaker": "Guest", "text": "Thanks.", "begin": 1.5, "end": 2.5},
        ]
    }
    transcript = parse(write(tmp_path, payload))
    speakers = [s.speaker_raw for s in transcript.segments]
    assert speakers == ["Host", "Guest"]


def test_google_stt_shape(tmp_path: Path) -> None:
    payload = {
        "results": [
            {"alternatives": [{"transcript": "Hello there.", "confidence": 0.95}], "channelTag": 1},
            {"alternatives": [{"transcript": "Hi back.", "confidence": 0.92}], "channelTag": 2},
        ]
    }
    transcript = parse(write(tmp_path, payload))
    assert len(transcript.segments) == 2
    assert transcript.segments[0].speaker_raw == "1"
    assert transcript.segments[0].confidence == 0.95


def test_deepgram_shape(tmp_path: Path) -> None:
    payload = {
        "results": {
            "channels": [
                {
                    "alternatives": [
                        {
                            "transcript": "fallback transcript",
                            "paragraphs": {
                                "paragraphs": [
                                    {
                                        "speaker": 0,
                                        "start": 0.0,
                                        "end": 2.0,
                                        "sentences": [{"text": "Welcome to the show."}],
                                    },
                                    {
                                        "speaker": 1,
                                        "start": 2.0,
                                        "end": 4.0,
                                        "sentences": [{"text": "Thanks for having me."}],
                                    },
                                ]
                            },
                        }
                    ]
                }
            ]
        }
    }
    transcript = parse(write(tmp_path, payload))
    assert len(transcript.segments) == 2
    assert transcript.segments[0].speaker_raw == "0"


def test_flat_list_shape(tmp_path: Path) -> None:
    payload = [
        {"speaker": "Alice", "text": "First."},
        {"speaker": "Bob", "text": "Second."},
    ]
    transcript = parse(write(tmp_path, payload))
    assert [s.speaker_raw for s in transcript.segments] == ["Alice", "Bob"]


def test_text_blob_fallback(tmp_path: Path) -> None:
    payload = {"text": "Speaker 1: Hi there.\nSpeaker 2: Hello."}
    transcript = parse(write(tmp_path, payload))
    speakers = [s.speaker_raw for s in transcript.segments]
    assert speakers == ["Speaker 1", "Speaker 2"]


def test_unknown_shape_raises(tmp_path: Path) -> None:
    payload = {"random": "structure"}
    with pytest.raises(ValueError, match="did not match any known"):
        parse(write(tmp_path, payload))


def test_invalid_json_raises(tmp_path: Path) -> None:
    p = tmp_path / "broken.json"
    p.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON"):
        parse(p)
