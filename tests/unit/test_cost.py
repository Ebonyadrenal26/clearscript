"""Tests for the cost estimator."""

from __future__ import annotations

from clearscript.core.cost import estimate_cost, list_known_models


def test_anthropic_opus_estimate_is_in_expected_range() -> None:
    # 10k input tokens via Opus: input ~$0.15, output ~$0.75 — total ~$0.90
    transcript = "X" * 40_000  # ~10k tokens (chars/4)
    est = estimate_cost(
        transcript_text=transcript,
        provider_type="anthropic",
        model="claude-opus-4-7",
    )
    assert est.pricing_known
    assert 0.5 < est.total_cost_usd < 1.5  # generous window
    assert est.input_tokens > 8000


def test_deepseek_chat_is_cheap() -> None:
    transcript = "X" * 40_000
    est = estimate_cost(
        transcript_text=transcript,
        provider_type="openai-compat",
        model="deepseek-chat",
    )
    assert est.pricing_known
    assert est.total_cost_usd < 0.05


def test_ollama_is_free() -> None:
    est = estimate_cost(
        transcript_text="hello world",
        provider_type="ollama",
        model="qwen2.5:14b",
    )
    assert est.pricing_known
    assert est.total_cost_usd == 0.0
    assert "local" in est.note


def test_unknown_model_returns_unknown_flag() -> None:
    est = estimate_cost(
        transcript_text="x" * 1000,
        provider_type="openai",
        model="gpt-99-imaginary",
    )
    assert not est.pricing_known
    assert est.total_cost_usd == 0.0
    assert "No pricing data" in est.note


def test_cjk_text_estimated_higher_than_ascii_for_same_chars() -> None:
    # 1000 CJK chars vs 1000 ASCII chars — CJK should produce more tokens
    cjk_est = estimate_cost(
        transcript_text="测" * 1000,
        provider_type="anthropic",
        model="claude-opus-4-7",
    )
    ascii_est = estimate_cost(
        transcript_text="X" * 1000,
        provider_type="anthropic",
        model="claude-opus-4-7",
    )
    assert cjk_est.input_tokens > ascii_est.input_tokens
    assert cjk_est.total_cost_usd > ascii_est.total_cost_usd


def test_known_models_listing_shape() -> None:
    known = list_known_models()
    assert "anthropic" in known
    assert "claude-opus-4-7" in known["anthropic"]
    assert "openai-compat" in known
    assert "deepseek-chat" in known["openai-compat"]


def test_as_dict_round_trip() -> None:
    est = estimate_cost(
        transcript_text="x" * 1000,
        provider_type="anthropic",
        model="claude-opus-4-7",
    )
    payload = est.as_dict()
    for key in (
        "input_tokens",
        "output_tokens_estimate",
        "input_cost_usd",
        "output_cost_usd",
        "total_cost_usd",
        "pricing_known",
        "note",
    ):
        assert key in payload
