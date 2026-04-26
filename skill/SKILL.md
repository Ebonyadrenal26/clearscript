---
name: clearscript
description: "Clean ASR-output transcripts into archive-grade text. Use whenever raw speech-to-text output (Whisper / Otter / Feishu Miaoji 飞书妙记 / Tongyi Tingwu 通义听悟 / PLAUD / Tencent Meeting / Yuanbao 元宝) needs cleanup. Common scenarios: VC reference checks, founder interviews, customer interviews, board / investment-committee recordings, internal meetings, podcast and media transcripts. Trigger on: 整理逐字稿, 清理稿子, 清理这份转录, reformat 访谈, ASR 稿子帮我处理一下, 整理这个录音, 把这段会议记录整理一下, 把录音整理成访谈稿, ref check 整理, clean transcript, fix ASR output, format interview transcript, normalize speakers, transcript cleanup. Also trigger when content shows speaker labels with conversational paragraphs, [Speaker N] markers, or VTT/SRT cue blocks, even without an explicit ask. Apply the 6+1 layered edit pass: L1 speaker normalization, L2 head/tail trim, L3 ASR error correction, L3.5 sentence-level reasoning cleanup, L4 information preservation, L5 dialogue formatting, L6 punctuation. Preserve 中英 code-switching verbatim. Batch all uncertainties into a single confirmation pass at the end. Output cleaned markdown plus a JSON change log plus a JSON list of suggested terminology-library additions for next time. Skill is the open-source companion to clearscript (https://github.com/Chen17-sq/clearscript), a local-first transcript editor; the standalone app uses these same prompts."
---

# clearscript

Open-source transcript-cleanup skill from [Chen17-sq/clearscript](https://github.com/Chen17-sq/clearscript). Drop this skill into any Claude agent (Claude Code, Claude Agent SDK, or any agent that loads markdown skills) and the agent gains a disciplined 7-layer transcript-editor that:

- normalizes speakers
- trims pre-/post-conversation chitchat and AI-generated summary blocks
- fixes ASR misrecognitions at word and phrase level
- preserves the speaker's original phrasing (no helpful paraphrasing)
- formats dialogue cleanly
- normalizes punctuation
- ends with a single batched confirmation pass instead of interrupting

## When to use this skill

Trigger any time the user provides:

- A raw transcript from any ASR tool (Whisper, Otter, Feishu Miaoji 飞书妙记, Tongyi Tingwu 通义听悟, PLAUD, Tencent Meeting, Yuanbao 元宝, AssemblyAI, Deepgram, Google STT, etc.)
- A `.docx` / `.txt` / `.md` / `.srt` / `.vtt` / `.json` file that contains a recorded conversation
- Conversational text with speaker labels (`Speaker 1:`, `[Speaker 2]`, `张三：`) or `<v Speaker>...</v>` VTT voice tags
- A request like "整理这份逐字稿", "clean up this transcript", "format this interview", "fix this ASR output", "把这段会议记录整理一下"

Do **not** trigger this skill for:

- Generating a transcript from audio (this is post-processing, not transcription)
- Summarizing a transcript (use a separate summarization skill — clearscript explicitly preserves verbose detail)
- Translating a transcript (clearscript preserves the speaker's language; do not translate)

## How to use it

1. **Read the prompt files in this order** before doing any work:
   - `prompts/system_base.md` — universal principles and discipline rules
   - `prompts/stages/04_layered_edit.md` — the core editing-stage contract (output format)
   - `prompts/layers/l1_speaker.md` through `l6_punct.md` — layer-by-layer rules
   - `references/speakers.md`, `references/asr-corrections.md`, `references/edit-patterns.md` — accumulated user-specific corrections (start empty; the user grows them session by session)

2. **Apply the layers in order, not interleaved**: finish L1 across the entire transcript, then L2, then L3, then L3.5, then L4, then L5, then L6. This sequencing is non-negotiable; skipping it causes regressions.

3. **Output exactly three sections**, separated by delimiter lines:

   ```
   <cleaned markdown transcript>

   ---CHANGELOG---
   [
     {"layer": "L1", "old": "[Speaker 2]", "new": "Eileen:", "reason": "matched user briefing", "confidence": 1.0},
     {"layer": "L3", "old": "DeFi", "new": "Dify", "reason": "library exact match", "confidence": 0.99},
     {"layer": "L3.5", "old": "我们我们当时", "new": "我们当时", "reason": "stutter dedup", "confidence": 0.95}
   ]

   ---SUGGESTIONS---
   [
     {"kind": "term", "canonical": "PingCAP", "type": "company", "domain": "ai-infra", "aliases_seen": ["PinkCup"], "rationale": "company referenced repeatedly; ASR consistently mishears the name"}
   ]
   ```

4. **Batch all uncertainties at the end** in a single message to the user. Do not interrupt mid-edit. Format like:

   ```
   I need 3 clarifications before finalizing:

   1. [00:14:33] "MAM-9" — is this "Mem9"? (matches your library entry)
   2. [00:22:10] Speaker name "刘星" — should this be "刘勋"? (briefing mentioned Liu Xun)
   3. Data conflict: "千次 query 0.8 元" at 00:31:45 vs "千次 0.5 元" at 00:48:20 — which is canonical?
   ```

## Red lines (anti-hallucination)

- **Never auto-complete** a sentence the speaker abandoned. Leave half-sentences as `[句子不完整: ...]` or `[unfinished: ...]`.
- **Never invent words** to fill `[inaudible]` / `[听不清]`. Mark and move on.
- **Never paraphrase** to make broken syntax flow. A broken sentence is data; a smoothed-over guess is fiction.
- **Never translate** code-switched English ↔ Chinese. Preserve both languages verbatim.
- **Never standardize** approximate phrasing ("差不多三四百人") into precise numbers ("约 350 人"). Approximation is signal.
- **Every correction must cite evidence**: a reference-database hit, briefing-confirmed context, or high-confidence semantic inference. "It sounds nicer" is not evidence.

## Output format conventions

- Speaker labels on their own line, no leading bullet, blank line before (except the first):

  ```
  Speaker 1:
  - first turn content here

  Speaker 2:
  - response content here
    - sub-bullet for nested points
  ```

- Bullets are short-dash `-`, never `•` or numbered.
- Chinese punctuation (`。 ，：；？！`) for Chinese-dominant sentences; ASCII for English-dominant.
- No interpretive annotations like `[语气强烈]` unless the user explicitly asks.

## Files in this skill

```
clearscript/
├── SKILL.md                              ← this file (loaded automatically)
├── prompts/
│   ├── system_base.md                    ← universal rules
│   ├── stages/
│   │   ├── 01_prescan.md
│   │   ├── 02_context_briefing.md
│   │   ├── 04_layered_edit.md            ← the main editing contract
│   │   ├── 06_self_review.md
│   │   ├── 07_batch_ask.md
│   │   └── 08_rescan.md
│   └── layers/
│       ├── l1_speaker.md
│       ├── l2_trim.md
│       ├── l3_asr_fix.md
│       ├── l3_5_sentence.md
│       ├── l4_preserve.md
│       ├── l5_format.md
│       └── l6_punct.md
├── references/
│   ├── speakers.md                       ← user's known speakers (starts empty)
│   ├── asr-corrections.md                ← user's accumulated ASR error → fix pairs
│   └── edit-patterns.md                  ← user's editing preferences
└── scripts/
    └── to_docx.py                        ← optional .docx exporter (requires python-docx)
```

## Companion product

For the same workflow with a graphical UI, project history, automatic library management, multi-format ingest (`.docx` / `.srt` / `.vtt` / `.json` / etc.), and bring-your-own-model support across 20+ providers:

- **Repo:** https://github.com/Chen17-sq/clearscript
- **Docs:** https://chen17-sq.github.io/clearscript/

The standalone app and this skill load **the same prompt files** — so when the standalone product's editing rules improve, this skill improves with the next release.

## License

MIT. See [LICENSE](https://github.com/Chen17-sq/clearscript/blob/main/LICENSE).
