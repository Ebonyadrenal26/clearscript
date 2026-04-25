"""Minimum-viable pipeline (v0.0.3).

Single-pass: ingest → compose prompts → call LLM once → parse output → write.

Library integration:
- Mode A (project-start activation): briefing text is scanned for entity hints
  (companies/products/speakers); each is looked up in the library and any
  matching aliases / related canonicals are added to the library_context block
  in the system prompt.
- Mode B (end-of-session harvest): the LLM is asked to emit a SUGGESTIONS
  block alongside the change log; pipeline parses it and exposes via
  ``EditResult.suggestions`` so the UI can ask the user to accept them.
- Mode C (in-flight learning): not in v0.0.x — needs the multi-stage pipeline
  with batch-ask. Tracked for v0.0.6.

The full multi-stage pipeline contract lives in ``docs/architecture.md``.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from clearscript.ingest import NormalizedTranscript, parse
from clearscript.prompts import compose_edit_prompt
from clearscript.providers import ChatMessage, LLMProvider

if TYPE_CHECKING:
    from clearscript.library import Library


@dataclass
class EditResult:
    edited_markdown: str
    change_log: list[dict[str, object]] = field(default_factory=list)
    suggestions: list[dict[str, object]] = field(default_factory=list)
    raw_response: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""
    provider: str = ""

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


CHANGELOG_DELIMITER = "---CHANGELOG---"
SUGGESTIONS_DELIMITER = "---SUGGESTIONS---"

# Heuristic: extract candidate entities from briefing text.
# Captures CamelCase tokens, ALL-CAPS acronyms, mixed letter+digit identifiers,
# and CJK names of plausible length.
_ENTITY_PATTERN = re.compile(
    r"[A-Z][a-zA-Z0-9]{2,}(?:[A-Z][a-zA-Z0-9]+)*"  # CamelCase: Dify, PingCAP
    r"|[A-Z]{2,}(?:-?\d+)?"  # ACRONYM: PMF, MAM-9
    r"|[一-鿿]{2,4}"  # CJK 2-4 char names: 张三, 君晨
)


@dataclass
class Pipeline:
    provider: LLMProvider
    model: str
    library: Library | None = None
    briefing_context: str = ""
    temperature: float = 0.0
    max_tokens: int = 8192

    def run(self, input_path: Path) -> EditResult:
        transcript = parse(input_path)
        return self.run_on_transcript(transcript)

    def run_on_transcript(self, transcript: NormalizedTranscript) -> EditResult:
        library_context = self._collect_library_context(transcript)
        system_prompt = compose_edit_prompt(
            briefing_context=self.briefing_context,
            library_context=library_context,
        )

        user_prompt = self._build_user_prompt(transcript)

        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_prompt),
        ]

        response = self.provider.chat(
            messages,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        edited, changelog, suggestions = self._split_output(response.text)

        return EditResult(
            edited_markdown=edited,
            change_log=changelog,
            suggestions=suggestions,
            raw_response=response.text,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            model=response.model,
            provider=response.provider,
        )

    def _build_user_prompt(self, transcript: NormalizedTranscript) -> str:
        return (
            "Apply the layered edit pipeline (L1 through L6, including L3.5) to the transcript "
            "below. Output the cleaned markdown transcript first, then the line "
            f"`{CHANGELOG_DELIMITER}` on its own line, then the JSON change log, then the line "
            f"`{SUGGESTIONS_DELIMITER}`, then the JSON list of library suggestions.\n\n"
            "Raw transcript:\n\n"
            "```\n"
            f"{transcript.to_markdown()}\n"
            "```"
        )

    def _collect_library_context(self, transcript: NormalizedTranscript) -> str:
        """Mode A: build a context block from library lookups on briefing seeds + detected speakers."""
        if self.library is None:
            return ""

        sections: list[str] = []

        # 1) Speakers detected in the raw transcript → library lookup
        speaker_lines: list[str] = []
        for spk in transcript.detected_speakers:
            hit = self.library.lookup_speaker(spk)
            if hit:
                speaker_lines.append(
                    f"- ASR speaker {spk!r} → use canonical label `{hit.display_label}` "
                    f"(real name: {hit.canonical_name})"
                )
        if speaker_lines:
            sections.append("Known speakers (from your library):\n" + "\n".join(speaker_lines))

        # 2) Entities from briefing → library lookup + alias hints
        if self.briefing_context:
            seen_canonicals: set[str] = set()
            term_lines: list[str] = []
            briefing_speaker_lines: list[str] = []

            for token in self._extract_entities(self.briefing_context):
                term_hit = self.library.lookup_alias(token)
                if term_hit and term_hit.canonical not in seen_canonicals:
                    term_lines.append(
                        f"- ASR may write {token!r} → canonical `{term_hit.canonical}` "
                        f"({term_hit.type or 'term'}, confidence {term_hit.confidence:.2f})"
                    )
                    seen_canonicals.add(term_hit.canonical)
                else:
                    spk_hit = self.library.lookup_speaker(token)
                    if spk_hit and spk_hit.canonical_name not in seen_canonicals:
                        briefing_speaker_lines.append(
                            f"- {token!r} → speaker label `{spk_hit.display_label}` "
                            f"(real name: {spk_hit.canonical_name})"
                        )
                        seen_canonicals.add(spk_hit.canonical_name)

            if term_lines:
                sections.append("Term mappings from your library:\n" + "\n".join(term_lines))
            if briefing_speaker_lines:
                sections.append(
                    "Briefing speakers found in your library:\n" + "\n".join(briefing_speaker_lines)
                )

        return "\n\n".join(sections)

    @staticmethod
    def _extract_entities(text: str) -> list[str]:
        """Heuristic extraction of candidate entity tokens from briefing text."""
        seen: set[str] = set()
        ordered: list[str] = []
        for match in _ENTITY_PATTERN.finditer(text):
            token = match.group(0).strip()
            if len(token) < 2 or token in seen:
                continue
            # Filter very common English words masquerading as proper nouns.
            if token.lower() in {"the", "and", "for", "with", "from", "into", "this", "that"}:
                continue
            seen.add(token)
            ordered.append(token)
        return ordered

    @staticmethod
    def _strip_json_fence(text: str) -> str:
        """Remove markdown code-fence wrapping if the model added it."""
        text = text.strip()
        if text.startswith("```"):
            lines = [line for line in text.splitlines() if not line.startswith("```")]
            text = "\n".join(lines).strip()
        return text

    @classmethod
    def _split_output(
        cls, text: str
    ) -> tuple[str, list[dict[str, object]], list[dict[str, object]]]:
        """Parse the model's three-section response: markdown / changelog / suggestions."""
        if CHANGELOG_DELIMITER not in text:
            return text.strip(), [], []

        edited_part, _, after_changelog = text.partition(CHANGELOG_DELIMITER)
        edited = edited_part.strip()

        if SUGGESTIONS_DELIMITER in after_changelog:
            changelog_part, _, suggestions_part = after_changelog.partition(SUGGESTIONS_DELIMITER)
        else:
            changelog_part = after_changelog
            suggestions_part = "[]"

        changelog = cls._parse_json_list(changelog_part)
        suggestions = cls._parse_json_list(suggestions_part)
        return edited, changelog, suggestions

    @classmethod
    def _parse_json_list(cls, text: str) -> list[dict[str, object]]:
        cleaned = cls._strip_json_fence(text)
        if not cleaned:
            return []
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            return []
        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, dict)]
        return []
