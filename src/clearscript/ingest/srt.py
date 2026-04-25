"""SubRip (.srt) subtitle adapter.

Subtitles come with start/end timestamps per cue. We preserve those on each
``Segment`` and attempt to extract a speaker label from the cue text using
common conventions (``John: hello``, ``[John] hello``, ``- hello``).
"""

from __future__ import annotations

import re
from pathlib import Path

import srt

from clearscript.ingest.base import IngestAdapter, NormalizedTranscript, Segment

_INLINE_SPEAKER_PATTERNS = [
    re.compile(r"^\s*\[([^\]]{1,40})\]\s*[:：]?\s*(.*)$"),
    re.compile(r"^\s*([^\s:：]{1,20}(?:\s[^\s:：]{1,20})?)\s*[:：]\s+(.+)$"),
]
# Strip subtitle styling: <i>, <b>, {\an1}, etc.
_STYLE_TAGS = re.compile(r"</?[a-zA-Z][^>]*>|\{[^}]+\}")


def _split_speaker(text: str) -> tuple[str | None, str]:
    text = _STYLE_TAGS.sub("", text).strip()
    for pat in _INLINE_SPEAKER_PATTERNS:
        m = pat.match(text)
        if m:
            speaker = m.group(1).strip()
            content = m.group(2).strip()
            if speaker and len(speaker) <= 25 and content:
                return speaker, content
    return None, text


def _td_to_seconds(td) -> float:
    return td.total_seconds()


class SrtAdapter(IngestAdapter):
    name = "srt"
    extensions = (".srt",)

    def matches(self, path: Path, head: str) -> bool:
        return path.suffix.lower() in self.extensions

    def parse(self, path: Path) -> NormalizedTranscript:
        content = path.read_text(encoding="utf-8")
        return self._parse_text(content, path)

    def parse_string(self, content: str, source_path: Path | None = None) -> NormalizedTranscript:
        return self._parse_text(content, source_path)

    def _parse_text(self, content: str, path: Path | None) -> NormalizedTranscript:
        cues = list(srt.parse(content))
        segments: list[Segment] = []
        seen_speakers: list[str] = []
        current_speaker: str | None = None
        current_lines: list[str] = []
        current_start: float | None = None
        current_end: float | None = None

        def flush() -> None:
            if current_lines:
                segments.append(
                    Segment(
                        text=" ".join(s for s in current_lines if s),
                        speaker_raw=current_speaker,
                        start_sec=current_start,
                        end_sec=current_end,
                    )
                )

        for cue in cues:
            text = (cue.content or "").replace("\n", " ").strip()
            if not text:
                continue
            speaker, body = _split_speaker(text)
            if speaker is not None and speaker != current_speaker:
                flush()
                current_speaker = speaker
                if speaker not in seen_speakers:
                    seen_speakers.append(speaker)
                current_lines = [body]
                current_start = _td_to_seconds(cue.start)
                current_end = _td_to_seconds(cue.end)
            else:
                if not current_lines:
                    current_start = _td_to_seconds(cue.start)
                current_end = _td_to_seconds(cue.end)
                current_lines.append(body)

        flush()

        duration = _td_to_seconds(cues[-1].end) if cues else None
        return NormalizedTranscript(
            segments=segments,
            source_format=self.name,
            source_path=path,
            detected_speakers=seen_speakers,
            duration_sec=duration,
        )
