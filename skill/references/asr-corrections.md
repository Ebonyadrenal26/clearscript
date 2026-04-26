# ASR corrections

Accumulated ASR transcription errors and their correct forms, confirmed against actual transcript editing sessions.

**How the skill uses this:** read this file at the start of every session. When scanning a transcript, match against this list **first** before doing context-based inference. If a candidate fix is in this list, apply it. If not, judge by context and add a SUGGESTIONS entry for review.

## Format

| ASR original | Correct form | Source / session |
|---|---|---|

Add rows as you confirm corrections.

## Categories worth tracking

- **Pro terms / management vocab** — e.g. spoken "skip level" misheard as "scalable"
- **Company / product names** — e.g. "Dify" misheard as "DeFi", "Manus" as "Minus"
- **Acronyms** — e.g. "GEO" as "GRU", "EAT" as "E-E-A-T"
- **Tech terms** — e.g. "JavaScript" as "Dust Script"
- **Names (Chinese / English)** — same person across multiple ASR transcriptions
- **Numbers / dates** — ASR sometimes reads dates as digit runs (e.g. `53531` → `2026-05-31`)
- **Generic / industry-vague substitutions** — context-only fixes

## Don't over-correct spoken style

- Keep colloquialisms: "蛮好的" (don't change to "很好"), "做事情" (don't change to "做事")
- Keep "you know" / "I mean" / "怎么说呢" — strip moderately for readability, leave 1-2 per paragraph
- Keep approximate numbers in original form: "差不多三四百人" stays as-is
