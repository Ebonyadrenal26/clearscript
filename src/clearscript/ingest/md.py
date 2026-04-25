"""Markdown ASR adapter.

Behaves like :class:`TxtAdapter` but with one extra capability: detect and
strip AI-generated summary blocks that ASR tools (Typeless, Yuanbao, Tongyi
Tingwu, Miaoji) like to prepend or append to their exports.
"""

from __future__ import annotations

import re
from pathlib import Path

from clearscript.ingest.base import IngestAdapter, NormalizedTranscript
from clearscript.ingest.txt import TxtAdapter

# Heuristic summary-block triggers (English + Chinese)
_SUMMARY_HEADER_PATTERNS = [
    re.compile(r"^#{1,3}\s*(summary|abstract|key\s*takeaway|key\s*point|tl;?dr)\b", re.IGNORECASE),
    re.compile(
        r"^#{1,3}\s*(本次访谈总结|会议总结|本次会议总结|会议要点|访谈要点|核心要点|关键要点|内容摘要|摘要|总结)"
    ),
    re.compile(
        r"^#{1,3}\s*(action\s*item|todo|next\s*step|后续(待办|事项|动作)|待办事项|action\s*items?)",
        re.IGNORECASE,
    ),
]

# Tool-injected provenance lines we want to nuke
_PROVENANCE_PATTERNS = [
    re.compile(r"^[*_>\s]*(generated|produced|exported)\s+(on|by|with).*$", re.IGNORECASE),
    re.compile(r"^[*_>\s]*由\s*(typeless|元宝|通义听悟|飞书妙记|腾讯会议|claude|chatgpt).*生成"),
]


def _strip_summary_blocks(text: str) -> str:
    """Remove ATX-heading-marked summary blocks while preserving the actual transcript.

    A "summary block" runs from the matched summary header until the next
    heading that is NOT itself a summary-style header (transcripts usually
    sit under headings like ``## Meeting`` / ``## Transcript`` / ``## 会议正文``
    that should re-open the keep stream), or until a speaker-pattern line.
    """
    lines = text.splitlines()
    keep: list[str] = []
    skip_active = False

    speaker_line = re.compile(r"^[\w一-龥\[][^\n]{0,40}?\s*[:：]\s+\S")

    for line in lines:
        stripped = line.lstrip()
        is_heading = stripped.startswith("#")
        is_summary_heading = is_heading and any(p.match(stripped) for p in _SUMMARY_HEADER_PATTERNS)

        if skip_active:
            # End the skip on any non-summary heading, or on the first speaker line.
            if (is_heading and not is_summary_heading) or speaker_line.match(stripped):
                skip_active = False
                # fall through and evaluate the line normally
            elif is_summary_heading:
                continue  # nested summary subsection — stay in skip mode
            else:
                continue

        if is_summary_heading:
            skip_active = True
            continue

        if any(p.match(stripped) for p in _PROVENANCE_PATTERNS):
            continue

        keep.append(line)

    cleaned = "\n".join(keep)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip() + "\n"


class MdAdapter(IngestAdapter):
    name = "md"
    extensions = (".md", ".markdown")

    def matches(self, path: Path, head: str) -> bool:
        return path.suffix.lower() in self.extensions

    def parse(self, path: Path) -> NormalizedTranscript:
        content = path.read_text(encoding="utf-8")
        return self.parse_string(content, path)

    def parse_string(self, content: str, source_path: Path | None = None) -> NormalizedTranscript:
        cleaned = _strip_summary_blocks(content)
        # Delegate to the txt adapter for speaker-line heuristics.
        result = TxtAdapter().parse_string(cleaned, source_path)
        result.source_format = self.name
        return result
