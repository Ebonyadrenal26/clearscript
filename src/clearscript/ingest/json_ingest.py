"""JSON ASR adapter.

Tries to recognize the most common JSON shapes that ASR tools emit:

1. **OpenAI Whisper API verbose_json / Faster-Whisper / WhisperX**:
   ``{"segments": [{"text": ..., "start": ..., "end": ..., "speaker": ...}], ...}``
2. **Google Cloud Speech-to-Text**:
   ``{"results": [{"alternatives": [{"transcript": ...}], "channelTag": 1}]}``
3. **Deepgram**:
   ``{"results": {"channels": [{"alternatives": [{"transcript": ..., "words": [...]}]}]}}``
4. **PLAUD**:
   ``{"transcripts": [{"speaker": ..., "text": ..., "begin": ...}]}``
5. **Generic flat list**:
   ``[{"speaker": ..., "text": ..., "start": ...}]``
6. **Single-string fallback**: ``{"text": "..."}`` or just ``"..."`` — passed
   through to the txt adapter for speaker heuristics.
"""

from __future__ import annotations

import json
from pathlib import Path

from clearscript.ingest.base import IngestAdapter, NormalizedTranscript, Segment
from clearscript.ingest.txt import TxtAdapter


def _segments_from_whisperish(payload: dict) -> list[Segment] | None:
    segments_raw = payload.get("segments")
    if not isinstance(segments_raw, list) or not segments_raw:
        return None
    out: list[Segment] = []
    for s in segments_raw:
        if not isinstance(s, dict):
            continue
        text = s.get("text") or s.get("transcript") or ""
        if not text:
            continue
        out.append(
            Segment(
                text=text.strip(),
                speaker_raw=s.get("speaker") or s.get("speaker_id"),
                start_sec=_safe_float(
                    s.get("start") if s.get("start") is not None else s.get("begin")
                ),
                end_sec=_safe_float(s.get("end")),
                confidence=_safe_float(
                    s.get("confidence") if s.get("confidence") is not None else s.get("avg_logprob")
                ),
            )
        )
    return out or None


def _segments_from_google_stt(payload: dict) -> list[Segment] | None:
    results = payload.get("results")
    if not isinstance(results, list) or not results:
        return None
    out: list[Segment] = []
    for r in results:
        alts = r.get("alternatives") if isinstance(r, dict) else None
        if not alts:
            continue
        first = alts[0]
        text = first.get("transcript") or ""
        if not text:
            continue
        out.append(
            Segment(
                text=text.strip(),
                speaker_raw=str(r.get("channelTag")) if r.get("channelTag") is not None else None,
                confidence=_safe_float(first.get("confidence")),
            )
        )
    return out or None


def _segments_from_deepgram(payload: dict) -> list[Segment] | None:
    results = payload.get("results")
    if not isinstance(results, dict):
        return None
    channels = results.get("channels")
    if not isinstance(channels, list) or not channels:
        return None
    alts = channels[0].get("alternatives") if isinstance(channels[0], dict) else None
    if not alts:
        return None
    paragraphs = (
        alts[0].get("paragraphs", {}).get("paragraphs") if alts[0].get("paragraphs") else None
    )
    if isinstance(paragraphs, list) and paragraphs:
        out: list[Segment] = []
        for para in paragraphs:
            if not isinstance(para, dict):
                continue
            sentences = para.get("sentences") or []
            text = " ".join(s.get("text", "") for s in sentences if isinstance(s, dict)).strip()
            if not text:
                continue
            out.append(
                Segment(
                    text=text,
                    speaker_raw=str(para.get("speaker"))
                    if para.get("speaker") is not None
                    else None,
                    start_sec=_safe_float(para.get("start")),
                    end_sec=_safe_float(para.get("end")),
                )
            )
        if out:
            return out
    transcript = alts[0].get("transcript")
    if transcript:
        return [Segment(text=transcript.strip())]
    return None


def _segments_from_plaud(payload: dict) -> list[Segment] | None:
    items = payload.get("transcripts") or payload.get("transcript")
    if not isinstance(items, list) or not items:
        return None
    out: list[Segment] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        text = item.get("text") or item.get("content")
        if not text:
            continue
        out.append(
            Segment(
                text=text.strip(),
                speaker_raw=item.get("speaker") or item.get("speakerName"),
                start_sec=_safe_float(
                    item.get("begin") if item.get("begin") is not None else item.get("start")
                ),
                end_sec=_safe_float(item.get("end")),
            )
        )
    return out or None


def _segments_from_flat_list(payload: list) -> list[Segment] | None:
    if not payload:
        return None
    out: list[Segment] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        text = item.get("text") or item.get("content") or item.get("transcript")
        if not text:
            continue
        out.append(
            Segment(
                text=text.strip(),
                speaker_raw=item.get("speaker") or item.get("speaker_id"),
                start_sec=_safe_float(
                    item.get("start") if item.get("start") is not None else item.get("begin")
                ),
                end_sec=_safe_float(item.get("end")),
            )
        )
    return out or None


def _safe_float(v) -> float | None:
    try:
        if v is None:
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


class JsonAdapter(IngestAdapter):
    name = "json"
    extensions = (".json",)

    def matches(self, path: Path, head: str) -> bool:
        return path.suffix.lower() in self.extensions

    def parse(self, path: Path) -> NormalizedTranscript:
        content = path.read_text(encoding="utf-8")
        return self.parse_string(content, path)

    def parse_string(self, content: str, source_path: Path | None = None) -> NormalizedTranscript:
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON: {exc}") from exc

        segments: list[Segment] | None = None
        if isinstance(payload, dict):
            for extractor in (
                _segments_from_whisperish,
                _segments_from_plaud,
                _segments_from_deepgram,
                _segments_from_google_stt,
            ):
                segments = extractor(payload)
                if segments:
                    break
            if segments is None and isinstance(payload.get("text"), str):
                # Single-blob fallback — let txt adapter try speaker heuristics.
                fallback = TxtAdapter().parse_string(payload["text"], source_path)
                fallback.source_format = self.name
                return fallback
        elif isinstance(payload, list):
            segments = _segments_from_flat_list(payload)
        elif isinstance(payload, str):
            fallback = TxtAdapter().parse_string(payload, source_path)
            fallback.source_format = self.name
            return fallback

        if not segments:
            raise ValueError(
                "JSON did not match any known ASR shape. Supported: Whisper-style "
                "{segments: [...]}, PLAUD {transcripts: [...]}, Google STT {results: [...]}, "
                "Deepgram, generic list of {speaker, text, start, end}."
            )

        seen_speakers: list[str] = []
        for seg in segments:
            if seg.speaker_raw and seg.speaker_raw not in seen_speakers:
                seen_speakers.append(seg.speaker_raw)

        duration = max((s.end_sec for s in segments if s.end_sec is not None), default=None)

        return NormalizedTranscript(
            segments=segments,
            source_format=self.name,
            source_path=source_path,
            detected_speakers=seen_speakers,
            duration_sec=duration,
        )
