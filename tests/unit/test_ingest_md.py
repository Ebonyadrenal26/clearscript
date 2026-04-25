"""Tests for the markdown ingest adapter."""

from __future__ import annotations

from pathlib import Path

from clearscript.ingest import parse


def write(tmp_path: Path, content: str, name: str = "t.md") -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def test_strips_ai_summary_block_at_top(tmp_path: Path) -> None:
    content = """## 本次访谈总结

- 受访人介绍了过往经历
- 公司当前规模约 300 人
- 主要竞品是 X 和 Y

## Transcript

Speaker 1: 你好。
Speaker 2: 你好啊。
"""
    transcript = parse(write(tmp_path, content))
    md = transcript.to_markdown()
    assert "本次访谈总结" not in md
    assert "受访人介绍" not in md
    assert "你好" in md


def test_strips_english_summary_block(tmp_path: Path) -> None:
    content = """# Summary

- Discussed product roadmap
- Action items pending

## Meeting

Speaker 1: Let's start.
Speaker 2: Okay.
"""
    transcript = parse(write(tmp_path, content))
    md = transcript.to_markdown()
    assert "Action items pending" not in md
    assert "Let's start" in md


def test_keeps_transcript_when_no_summary(tmp_path: Path) -> None:
    content = """Speaker 1: Hi.
Speaker 2: Hello.
"""
    transcript = parse(write(tmp_path, content))
    md = transcript.to_markdown()
    assert "Speaker 1" in md
    assert "Hi." in md


def test_strips_provenance_line(tmp_path: Path) -> None:
    content = """*Generated on 2026-04-25 by Typeless*

Speaker 1: Hi.
"""
    transcript = parse(write(tmp_path, content))
    md = transcript.to_markdown()
    assert "Typeless" not in md
    assert "Hi." in md


def test_format_marker_is_md(tmp_path: Path) -> None:
    transcript = parse(write(tmp_path, "Speaker 1: Hi.\n"))
    assert transcript.source_format == "md"
