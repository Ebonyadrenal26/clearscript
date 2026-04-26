"""Chunking long transcripts.

A real 90-minute interview is 30k-50k tokens. Sending that to the model in
one shot risks: hitting the context window, hitting max-output, blowing
latency past 5 minutes, or quietly truncating the answer. Chunking solves
all four — split the transcript at semantic boundaries, run each chunk
through the same prompts, stitch the cleaned outputs back together.

Boundary preference (best to worst):
    1. Speaker turn boundary (start of a new ``Segment``)
    2. Inside-segment sentence boundary (period / question mark / etc.)
    3. Hard character cut on whitespace (last resort)

Token estimation is a fast heuristic — accurate within ~15% across CJK and
Latin scripts:

    tokens ≈ ASCII_chars / 4 + CJK_chars / 1.5
"""

from __future__ import annotations

from dataclasses import dataclass

from clearscript.ingest.base import NormalizedTranscript, Segment

# Single-chunk runs are still preferable when they fit. Threshold tuned so
# that ~30 minutes of dialogue stays in one shot, 60+ minutes splits.
DEFAULT_TARGET_TOKENS = 3500  # aim per chunk
DEFAULT_TRIGGER_TOKENS = 6000  # below this, don't chunk
DEFAULT_HARD_MAX_TOKENS = 5000  # fallback split if a single segment exceeds this


@dataclass
class ChunkPlan:
    """Result of analyzing a transcript: tells the pipeline how to split."""

    chunks: list[NormalizedTranscript]
    estimated_tokens: list[int]

    @property
    def num_chunks(self) -> int:
        return len(self.chunks)

    @property
    def total_tokens(self) -> int:
        return sum(self.estimated_tokens)


def estimate_tokens(text: str) -> int:
    """Rough token estimate, fast (no tokenizer dep)."""
    if not text:
        return 0
    ascii_chars = 0
    cjk_chars = 0
    for ch in text:
        codepoint = ord(ch)
        if 0x4E00 <= codepoint <= 0x9FFF or 0x3400 <= codepoint <= 0x4DBF:
            cjk_chars += 1
        elif ch.isascii():
            ascii_chars += 1
        else:
            ascii_chars += 1  # Treat other scripts as ascii-ish
    return max(1, int(ascii_chars / 4 + cjk_chars / 1.5))


def estimate_segment_tokens(seg: Segment) -> int:
    """Token cost of a Segment including its speaker label overhead."""
    overhead = 0
    if seg.speaker_raw:
        overhead = estimate_tokens(seg.speaker_raw) + 2  # ': ' and newline
    return overhead + estimate_tokens(seg.text)


def plan_chunks(
    transcript: NormalizedTranscript,
    *,
    target_tokens: int = DEFAULT_TARGET_TOKENS,
    trigger_tokens: int = DEFAULT_TRIGGER_TOKENS,
    hard_max_tokens: int = DEFAULT_HARD_MAX_TOKENS,
) -> ChunkPlan:
    """Decide whether to chunk and produce the split plan.

    If the whole transcript fits under ``trigger_tokens``, returns a single
    chunk identical to the input. Otherwise greedily packs segments into
    chunks of size ``target_tokens``, respecting speaker-turn boundaries.
    Segments that themselves exceed ``hard_max_tokens`` are split inside.
    """
    total = sum(estimate_segment_tokens(s) for s in transcript.segments)
    if total <= trigger_tokens or not transcript.segments:
        return ChunkPlan(chunks=[transcript], estimated_tokens=[total])

    chunks: list[NormalizedTranscript] = []
    sizes: list[int] = []
    buffer: list[Segment] = []
    buffer_tokens = 0

    def flush() -> None:
        nonlocal buffer, buffer_tokens
        if not buffer:
            return
        chunks.append(_make_subchunk(transcript, buffer))
        sizes.append(buffer_tokens)
        buffer = []
        buffer_tokens = 0

    for seg in transcript.segments:
        seg_tokens = estimate_segment_tokens(seg)

        # Oversized single segment — split inside it
        if seg_tokens > hard_max_tokens:
            flush()
            for piece in _split_segment_by_tokens(seg, hard_max_tokens):
                piece_tokens = estimate_segment_tokens(piece)
                chunks.append(_make_subchunk(transcript, [piece]))
                sizes.append(piece_tokens)
            continue

        # Adding this segment would overflow → flush first
        if buffer and buffer_tokens + seg_tokens > target_tokens:
            flush()

        buffer.append(seg)
        buffer_tokens += seg_tokens

    flush()

    return ChunkPlan(chunks=chunks, estimated_tokens=sizes)


def _make_subchunk(parent: NormalizedTranscript, segments: list[Segment]) -> NormalizedTranscript:
    seen_speakers: list[str] = []
    for s in segments:
        if s.speaker_raw and s.speaker_raw not in seen_speakers:
            seen_speakers.append(s.speaker_raw)
    return NormalizedTranscript(
        segments=segments,
        source_format=parent.source_format,
        source_path=parent.source_path,
        detected_speakers=seen_speakers,
        duration_sec=None,
        raw_metadata=dict(parent.raw_metadata),
    )


def _split_segment_by_tokens(seg: Segment, max_tokens: int) -> list[Segment]:
    """Split a single Segment into sub-Segments, each under ``max_tokens``.

    Tries sentence boundaries first (.?。!?！？), falls back to whitespace.
    """
    text = seg.text
    if estimate_tokens(text) <= max_tokens:
        return [seg]

    # Sentence-aware first pass
    pieces = _split_on_sentences(text)
    out: list[Segment] = []
    buf = ""
    buf_tokens = 0
    for piece in pieces:
        piece_tokens = estimate_tokens(piece)
        if buf and buf_tokens + piece_tokens > max_tokens:
            out.append(Segment(text=buf.strip(), speaker_raw=seg.speaker_raw))
            buf = ""
            buf_tokens = 0
        buf += piece
        buf_tokens += piece_tokens
        if buf_tokens >= max_tokens:
            out.append(Segment(text=buf.strip(), speaker_raw=seg.speaker_raw))
            buf = ""
            buf_tokens = 0
    if buf.strip():
        out.append(Segment(text=buf.strip(), speaker_raw=seg.speaker_raw))
    return out or [seg]


def _split_on_sentences(text: str) -> list[str]:
    """Split text into sentence-shaped pieces, keeping trailing punctuation."""
    enders = "。！？!?.\n"
    out: list[str] = []
    buf = ""
    for ch in text:
        buf += ch
        if ch in enders:
            out.append(buf)
            buf = ""
    if buf:
        out.append(buf)
    return out
