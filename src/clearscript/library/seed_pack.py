"""Universal seed pack — common ASR errors that any user benefits from.

These are the patterns that show up over and over again across hundreds of
real interview transcripts: an ASR tool consistently mis-hears a known
company / product / tech term as something else.

The pack is loaded into a fresh library on first use so the user doesn't
have to teach clearscript what "DeFi → Dify" means before getting useful
output. After loading, the user grows their *personal* library on top.

Each entry has been verified against actual mis-transcriptions; we don't
include speculative guesses. Source data anonymized — names of source
sessions stripped — but the canonicals/aliases are real.
"""

from __future__ import annotations

# Format: (canonical, [aliases...], type, domain)
SEED_TERMS: list[tuple[str, list[str], str | None, str | None]] = [
    # AI / ML companies and products
    ("Dify", ["DeFi", "底牌", "Difan", "抵帆"], "company", "ai-infra"),
    ("Manus", ["Minus"], "company", "ai-infra"),
    ("Tavily", ["Tabby", "Tabli", "Tably"], "company", "ai-infra"),
    ("OpenClaw", ["OpenCloud", "OpenCrawl", "OpenClod"], "company", "ai-infra"),
    ("Mem0", ["MAM-9", "Mem9", "Mam9", "妈姆9", "妈姆零"], "product", "ai-infra"),
    ("Nebius", ["Nubians"], "company", "ai-infra"),
    ("PingCAP", ["PinkCup", "PingCup", "PingCop"], "company", "ai-infra"),
    ("Exa", ["Alexa", "X3", "Aeexa"], "company", "ai-infra"),
    ("Brave", ["Braun"], "company", "ai-infra"),
    ("Anthropic", ["iShopee"], "company", "ai-infra"),
    # Tech terms
    ("JavaScript", ["Dust Script", "JavaScrip"], "jargon", "ai-infra"),
    ("web search", ["WebSphere"], "jargon", "ai-infra"),
    ("E-E-A-T", ["EAT", "double E A T"], "acronym", None),
    # Management / product vocabulary
    ("skip level", ["scalable"], "jargon", None),
    ("PMF", ["PNF", "PMS"], "acronym", "vc"),
    ("GEO", ["GRU"], "acronym", "ai-infra"),
    ("SLG", ["SOG"], "acronym", "vc"),
]

# Format: (text, do_not_change_to, domain, reason)
SEED_NEGATIVES: list[tuple[str, str | None, str | None, str]] = [
    ("蛮好的", "很好", None, "preserve speaker's colloquial style"),
    ("做事情", "做事", None, "preserve speaker's colloquial style"),
    (
        "差不多三四百人",
        None,
        None,
        "preserve approximate phrasing — don't standardize to a precise number",
    ),
]


def is_library_empty(library) -> bool:
    """Check if the library has any user-added content (terms or speakers)."""
    stats = library.stats()
    return (stats.get("terms", 0) == 0) and (stats.get("speakers", 0) == 0)


def install_seed_pack(library, *, only_if_empty: bool = True) -> dict:
    """Insert the seed pack into the library if appropriate.

    Returns a summary dict: ``{terms: int, negatives: int, skipped: bool}``.
    """
    if only_if_empty and not is_library_empty(library):
        return {"terms": 0, "negatives": 0, "skipped": True}

    n_terms = 0
    for canonical, aliases, type_, domain in SEED_TERMS:
        library.add_term(
            canonical=canonical,
            aliases=aliases,
            type_=type_,
            domain=domain,
        )
        n_terms += 1

    n_negatives = 0
    for text, target, domain, reason in SEED_NEGATIVES:
        library.add_negative(
            text=text,
            do_not_change_to=target,
            domain=domain,
            reason=reason,
        )
        n_negatives += 1

    return {"terms": n_terms, "negatives": n_negatives, "skipped": False}
