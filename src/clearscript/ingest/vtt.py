"""WebVTT (.vtt) subtitle adapter.

Custom parser (rather than relying on a third-party lib) so we can preserve
``<v Speaker>...</v>`` voice tags — those are the canonical way VTT carries
speaker metadata, and many libraries strip them on parse.
"""

from __future__ import annotations

import re
from pathlib import Path

from clearscript.ingest.base import IngestAdapter, NormalizedTranscript, Segment
from clearscript.ingest.srt import _split_speaker

_TIMING_LINE = re.compile(
    r"^\s*(\d{1,2}:\d{2}(?::\d{2})?(?:\.\d{1,3})?)\s*-->\s*(\d{1,2}:\d{2}(?::\d{2})?(?:\.\d{1,3})?)"
)
_VOICE_TAG_OPEN = re.compile(r"<v\s+([^>]+?)>", re.IGNORECASE)
_VOICE_TAG_CLOSE = re.compile(r"</v>", re.IGNORECASE)
_OTHER_TAGS = re.compile(r"<(?!/?v\b)[^>]+>")


def _hms_to_seconds(s: str) -> float:
    parts = s.split(":")
    if len(parts) == 3:
        h, m, sec = parts
        return int(h) * 3600 + int(m) * 60 + float(sec)
    if len(parts) == 2:
        m, sec = parts
        return int(m) * 60 + float(sec)
    return float(parts[0])


def _extract_voice_speaker(text: str) -> tuple[str | None, str]:
    m = _VOICE_TAG_OPEN.search(text)
    if not m:
        return None, _OTHER_TAGS.sub("", text).strip()
    speaker = m.group(1).strip()
    cleaned = _VOICE_TAG_OPEN.sub("", text, count=1)
    cleaned = _VOICE_TAG_CLOSE.sub("", cleaned)
    cleaned = _OTHER_TAGS.sub("", cleaned)
    return speaker, cleaned.strip()


class VttAdapter(IngestAdapter):
    name = "vtt"
    extensions = (".vtt",)

    def matches(self, path: Path, head: str) -> bool:
        if path.suffix.lower() in self.extensions:
            return True
        return head.lstrip().startswith("WEBVTT")

    def parse(self, path: Path) -> NormalizedTranscript:
        return self.parse_string(path.read_text(encoding="utf-8"), path)

    def parse_string(self, content: str, source_path: Path | None = None) -> NormalizedTranscript:
        cues: list[tuple[float, float, str]] = []  # (start, end, raw_text)

        # Split into blocks separated by blank lines, ignoring the "WEBVTT" header
        blocks = re.split(r"\r?\n\s*\r?\n", content.strip())
        for block in blocks:
            if not block.strip() or block.startswith("WEBVTT"):
                continue
            lines = [ln for ln in block.splitlines() if ln.strip()]
            timing_idx = next((i for i, ln in enumerate(lines) if _TIMING_LINE.match(ln)), None)
            if timing_idx is None:
                continue
            timing_match = _TIMING_LINE.match(lines[timing_idx])
            if not timing_match:
                continue
            start = _hms_to_seconds(timing_match.group(1))
            end = _hms_to_seconds(timing_match.group(2))
            text = " ".join(lines[timing_idx + 1 :]).strip()
            if text:
                cues.append((start, end, text))

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

        for start, end, raw in cues:
            voice_speaker, voice_body = _extract_voice_speaker(raw)
            if voice_speaker:
                speaker, body = voice_speaker, voice_body
            else:
                speaker, body = _split_speaker(raw)

            if speaker is not None and speaker != current_speaker:
                flush()
                current_speaker = speaker
                if speaker not in seen_speakers:
                    seen_speakers.append(speaker)
                current_lines = [body]
                current_start = start
                current_end = end
            else:
                if not current_lines:
                    current_start = start
                current_end = end
                current_lines.append(body)

        flush()

        duration = cues[-1][1] if cues else None
        return NormalizedTranscript(
            segments=segments,
            source_format=self.name,
            source_path=source_path,
            detected_speakers=seen_speakers,
            duration_sec=duration,
        )
