"""Tests for the pipeline using the mock provider."""

from __future__ import annotations

from pathlib import Path

from clearscript.core.pipeline import Pipeline

MOCK_OUTPUT = """Speaker 1：
- Hi everyone, can you hear me?

Speaker 2：
- Yes I can.

---CHANGELOG---
[
  {"layer": "L1", "old": "Speaker 1:", "new": "Speaker 1：", "reason": "punctuation normalization", "confidence": 1.0}
]

---SUGGESTIONS---
[
  {"kind": "term", "canonical": "PingCAP", "type": "company", "domain": "ai-infra", "aliases_seen": ["PinkCup"]},
  {"kind": "speaker", "canonical_name": "Eileen", "display_label": "Eileen：", "aliases_seen": ["Speaker 2"]}
]
"""


def test_pipeline_runs_end_to_end(tmp_path: Path, mock_provider) -> None:
    mock_provider.response_text = MOCK_OUTPUT
    input_path = tmp_path / "transcript.txt"
    input_path.write_text(
        "Speaker 1: Hi everyone, can you hear me?\nSpeaker 2: Yes I can.\n",
        encoding="utf-8",
    )

    pipeline = Pipeline(provider=mock_provider, model="mock-model")
    result = pipeline.run(input_path)

    assert "Speaker 1：" in result.edited_markdown
    assert "Hi everyone" in result.edited_markdown
    assert len(result.change_log) == 1
    assert result.change_log[0]["layer"] == "L1"
    assert result.input_tokens == 100
    assert result.output_tokens == 50


def test_pipeline_handles_no_changelog(tmp_path: Path, mock_provider) -> None:
    mock_provider.response_text = "Just markdown, no changelog."
    input_path = tmp_path / "transcript.txt"
    input_path.write_text("Speaker 1: Hi.\n", encoding="utf-8")
    pipeline = Pipeline(provider=mock_provider, model="mock-model")
    result = pipeline.run(input_path)
    assert "Just markdown" in result.edited_markdown
    assert result.change_log == []


def test_pipeline_uses_library_speaker_mapping(tmp_path: Path, mock_provider, tmp_library) -> None:
    tmp_library.add_speaker(
        canonical_name="Eileen", display_label="Eileen：", aliases=["Speaker 2"]
    )
    mock_provider.response_text = "Output\n---CHANGELOG---\n[]"

    input_path = tmp_path / "transcript.txt"
    input_path.write_text("Speaker 2: Hi.\n", encoding="utf-8")
    pipeline = Pipeline(provider=mock_provider, model="mock-model", library=tmp_library)
    pipeline.run(input_path)

    system_msg = mock_provider.calls[0][0]
    assert "Speaker 2" in system_msg.content
    assert "Eileen" in system_msg.content


def test_pipeline_parses_suggestions(tmp_path: Path, mock_provider) -> None:
    """Mode B: SUGGESTIONS block is parsed into EditResult.suggestions."""
    mock_provider.response_text = MOCK_OUTPUT
    input_path = tmp_path / "t.txt"
    input_path.write_text("Speaker 1: Hi.\n", encoding="utf-8")
    pipeline = Pipeline(provider=mock_provider, model="mock-model")
    result = pipeline.run(input_path)

    assert len(result.suggestions) == 2
    kinds = sorted(s["kind"] for s in result.suggestions)
    assert kinds == ["speaker", "term"]
    term = next(s for s in result.suggestions if s["kind"] == "term")
    assert term["canonical"] == "PingCAP"
    assert "PinkCup" in term["aliases_seen"]


def test_pipeline_empty_suggestions(tmp_path: Path, mock_provider) -> None:
    mock_provider.response_text = "Output\n---CHANGELOG---\n[]\n---SUGGESTIONS---\n[]"
    input_path = tmp_path / "t.txt"
    input_path.write_text("Speaker 1: Hi.\n", encoding="utf-8")
    pipeline = Pipeline(provider=mock_provider, model="mock-model")
    result = pipeline.run(input_path)
    assert result.suggestions == []


def test_pipeline_extract_entities() -> None:
    """Mode A: briefing entity extraction picks up CamelCase, acronyms, and CJK names."""
    text = (
        "Speaker 1 = Siqi (host); Speaker 2 = Eileen (founder of Acme); "
        "seed terms: Dify, Manus, Mem9, MAM-9, PMF, 张三, 君晨"
    )
    entities = Pipeline._extract_entities(text)
    for token in ("Siqi", "Eileen", "Acme", "Dify", "Manus", "Mem9", "PMF", "张三", "君晨"):
        assert token in entities, f"missing: {token}"


def test_pipeline_briefing_seeds_pulled_into_context(
    tmp_path: Path, mock_provider, tmp_library
) -> None:
    """Mode A end-to-end: term in briefing gets looked up and added to system prompt."""
    tmp_library.add_term(canonical="Dify", aliases=["DeFi"], type_="company", domain="ai-infra")
    mock_provider.response_text = "Output\n---CHANGELOG---\n[]\n---SUGGESTIONS---\n[]"

    input_path = tmp_path / "t.txt"
    input_path.write_text("Speaker 1: hello.\n", encoding="utf-8")
    pipeline = Pipeline(
        provider=mock_provider,
        model="mock-model",
        library=tmp_library,
        briefing_context="Speaker 1 = host; companies discussed: Dify, Manus",
    )
    pipeline.run(input_path)

    system_msg = mock_provider.calls[0][0]
    assert "Term mappings from your library" in system_msg.content
    assert "Dify" in system_msg.content


def test_pipeline_split_output_handles_no_suggestions_section(mock_provider) -> None:
    text = "Edited text\n---CHANGELOG---\n[]"
    edited, changelog, suggestions = Pipeline._split_output(text)
    assert edited == "Edited text"
    assert changelog == []
    assert suggestions == []


def test_pipeline_split_output_handles_fenced_json(mock_provider) -> None:
    text = (
        "Edited\n"
        "---CHANGELOG---\n"
        '```json\n[{"layer": "L1", "old": "a", "new": "b"}]\n```\n'
        "---SUGGESTIONS---\n"
        '```json\n[{"kind": "term", "canonical": "X"}]\n```\n'
    )
    _edited, changelog, suggestions = Pipeline._split_output(text)
    assert len(changelog) == 1
    assert len(suggestions) == 1
    assert suggestions[0]["canonical"] == "X"
