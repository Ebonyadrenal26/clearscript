"""Ingest adapter registry and dispatch.

Detection is layered: extension first, content sniffing second. The first
adapter to ``matches()`` wins.
"""

from __future__ import annotations

from pathlib import Path

from clearscript.ingest.base import IngestAdapter, NormalizedTranscript
from clearscript.ingest.docx_ingest import DocxAdapter
from clearscript.ingest.json_ingest import JsonAdapter
from clearscript.ingest.md import MdAdapter
from clearscript.ingest.srt import SrtAdapter
from clearscript.ingest.txt import TxtAdapter
from clearscript.ingest.vtt import VttAdapter

# Order matters: more-specific adapters first, generic .txt fallback last.
_ADAPTERS: list[IngestAdapter] = [
    MdAdapter(),
    DocxAdapter(),
    SrtAdapter(),
    VttAdapter(),
    JsonAdapter(),
    TxtAdapter(),
]


def register_adapter(adapter: IngestAdapter) -> None:
    """Register a custom adapter (used by user plugins). Inserted ahead of all built-ins."""
    _ADAPTERS.insert(0, adapter)


def supported_extensions() -> list[str]:
    """All file extensions any adapter claims (used by the web UI file picker)."""
    seen: set[str] = set()
    out: list[str] = []
    for adapter in _ADAPTERS:
        for ext in adapter.extensions:
            if ext not in seen:
                seen.add(ext)
                out.append(ext)
    return out


def detect_format(path: Path) -> IngestAdapter:
    """Return the first adapter that claims the file."""
    head = ""
    if path.is_file():
        try:
            head = path.read_text(encoding="utf-8", errors="ignore")[:4096]
        except OSError:
            head = ""

    for adapter in _ADAPTERS:
        if adapter.matches(path, head):
            return adapter

    raise ValueError(
        f"No ingest adapter matched {path}. Supported extensions: {supported_extensions()}"
    )


def parse(path: Path) -> NormalizedTranscript:
    """Parse a file into a NormalizedTranscript using the right adapter."""
    adapter = detect_format(path)
    return adapter.parse(path)
