"""DOCX ASR adapter.

Reads a Word document, extracts paragraphs in order, and runs them through
the same speaker-line heuristics as the txt adapter. Has a soft fallback:
if a paragraph has a leading bold run that looks like a name, treat the bold
text as the speaker label.

Tools whose export this aims to handle out-of-box:
- 飞书妙记 (Feishu Miaoji) — exports docx with speaker name in bold + timestamp
- 腾讯会议 (Tencent Meeting) — exports docx with speaker name + colon
- 通义听悟 (Tongyi Tingwu) — exports docx with speaker label per paragraph
- Generic Word docs from any source
"""

from __future__ import annotations

import re
from pathlib import Path

from docx import Document

from clearscript.ingest.base import IngestAdapter, NormalizedTranscript
from clearscript.ingest.txt import TxtAdapter

_TIMESTAMP_INLINE_PATTERN = re.compile(
    r"^\s*\(?\[?\d{1,2}[:：]\d{2}(?:[:：]\d{2})?(?:\.\d+)?\]?\)?\s*"
)


def _extract_paragraphs(path: Path) -> list[str]:
    """Pull paragraphs from a .docx, with light Feishu-Miaoji-aware handling.

    For each paragraph:
    - If the first run is bold and looks like a speaker name (short, no
      sentence-ending punctuation), treat the bold text as the speaker label
      and synthesize ``Name: rest`` so downstream txt heuristics catch it.
    - Otherwise yield the paragraph text as-is.
    - Strip leading inline timestamps like ``00:14:33`` or ``[0:14:33]``.
    """
    doc = Document(str(path))
    out: list[str] = []
    for para in doc.paragraphs:
        text = para.text or ""
        text = _TIMESTAMP_INLINE_PATTERN.sub("", text, count=1)
        text = text.strip()
        if not text:
            out.append("")
            continue

        bold_speaker = _try_extract_bold_speaker(para)
        if bold_speaker:
            label, rest = bold_speaker
            if rest:
                out.append(f"{label}: {rest}")
            else:
                out.append(f"{label}:")
        else:
            out.append(text)
    return out


def _try_extract_bold_speaker(para) -> tuple[str, str] | None:
    """If the paragraph leads with a bold-styled name-like run, return (label, rest)."""
    runs = list(para.runs)
    if not runs:
        return None

    # Concatenate adjacent leading-bold runs
    bold_text = ""
    rest_text = ""
    seen_unbold = False
    for run in runs:
        if not seen_unbold and run.bold:
            bold_text += run.text or ""
        else:
            seen_unbold = True
            rest_text += run.text or ""

    bold_text = bold_text.strip().rstrip("：:").strip()
    rest_text = rest_text.strip()

    if not bold_text:
        return None
    if len(bold_text) > 30:
        return None
    if any(ch in bold_text for ch in "。.!?！？"):
        return None
    # If there's no rest, this might just be a bold heading line, not a speaker —
    # only treat as speaker if it looks like a short name.
    if not rest_text and len(bold_text) > 12:
        return None
    return bold_text, rest_text


class DocxAdapter(IngestAdapter):
    name = "docx"
    extensions = (".docx",)

    def matches(self, path: Path, head: str) -> bool:
        return path.suffix.lower() in self.extensions

    def parse(self, path: Path) -> NormalizedTranscript:
        paragraphs = _extract_paragraphs(path)
        merged = "\n".join(paragraphs)
        result = TxtAdapter().parse_string(merged, path)
        result.source_format = self.name
        return result
