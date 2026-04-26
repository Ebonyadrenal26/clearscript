---
hide:
  - navigation
  - toc
---

<div class="bh-hero" markdown="1">
![clearscript banner — local-first ASR transcript editor](assets/banner.svg)
</div>

<div class="bh-pills" markdown="1">
<span class="bh-pill bh-pill--red">PYTHON</span>
<span class="bh-pill bh-pill--blue">SVELTEKIT</span>
<span class="bh-pill bh-pill--yellow">SQLITE</span>
<span class="bh-pill bh-pill--white">MIT</span>
</div>

# You just spent 45 minutes fixing the same transcript errors. Again.

Your ASR tool gives you 95% of the transcript right. The other 5% is mind-numbing:

- "Speaker 2" never gets a real name
- "Dify" came back as "DeFi"
- "PingCAP" came back as "PinkCup"
- The mic-check pleasantries you delete every time
- The same misheard jargon you fixed last week

Then tomorrow you'll do another interview and start over.

## clearscript watches you fix it once. Next time, it remembers.

Drop in a raw transcript → pick any model → click Run → edit inline → download `.docx`. Your fixes go into a local terminology library. By run #10 you barely touch anything.

This started as a personal Claude skill that ran on a few hundred VC reference checks, founder interviews, board meetings, and podcast cleanups. The library learned. The 45 minutes shrank. Now it's MIT-licensed, local-first, and yours to use.

<div class="bh-features" markdown="1">

<div class="bh-feature bh-feature--red" markdown="1">
### <span class="bh-feature__color"></span> Local-first
Transcripts and the terminology library live on your disk. No accounts, no telemetry, no cloud dependency. The only network call is the one you authorize — your chosen LLM provider.
</div>

<div class="bh-feature bh-feature--blue" markdown="1">
### <span class="bh-feature__color"></span> Bring your own model
Five adapters cover **20+ services**: Anthropic · OpenAI · DeepSeek · Moonshot · Qwen · Together · Groq · Fireworks · Mistral · OpenRouter · Gemini · Ollama · llama.cpp · LM Studio · custom endpoints.
</div>

<div class="bh-feature bh-feature--yellow" markdown="1">
### <span class="bh-feature__color"></span> Compounding library
A local SQLite knowledge base of terms, speakers, and edit patterns that grows with every session. Next session pre-loads the relevant subset automatically. Markdown views auto-export — human-readable, git-trackable.
</div>

</div>

---

## Why it exists

Existing transcript-cleanup tools fall into two camps:

- **Cloud SaaS** (Otter, Rev, Sonix): your audio and text get uploaded, processed by a closed model, and stored on someone else's servers. Privacy is a checkbox, not an architecture.
- **Generic LLM chats** (paste into ChatGPT): every session starts from zero. The model has no memory of who your speakers are, what your industry's jargon looks like, or which corrections you've made a hundred times before.

clearscript is the third option:

|                                  | Cloud SaaS | Plain LLM | **clearscript**          |
| -------------------------------- | :--------: | :-------: | :----------------------: |
| Data stays local                 |    ✗       |    ✗      | **✓**                    |
| Bring your own model             |    ✗       |    ✗      | **✓**                    |
| Works offline (with local model) |    ✗       |    ✗      | **✓**                    |
| Compounding terminology library  |    ✗       |    ✗      | **✓**                    |
| Reproducible / audit trail       |    ✗       |    ✗      | **✓**                    |
| Multi-format input/output        |  partial   |    ✗      | **✓**                    |

---

## Quick start

```bash
git clone https://github.com/Chen17-sq/clearscript.git
cd clearscript
uv sync
export ANTHROPIC_API_KEY=sk-ant-...   # or DEEPSEEK_API_KEY / OPENAI_API_KEY / GEMINI_API_KEY
uv run clearscript serve
```

Opens **http://127.0.0.1:7681** in your browser. Bauhaus-styled single-page interface: pick a provider pill, paste or drag in your transcript, click **Clean transcript**, edit inline, download as `.md` / `.docx`.

→ See the full [Quickstart](quickstart.md) for the 5-minute walkthrough.

---

## Supported input formats

| Format | Source examples |
| --- | --- |
| `.txt` | Generic, with speaker-label heuristics |
| `.md` | Auto-strips AI-summary blocks (English + Chinese) |
| `.docx` | 飞书妙记 / 腾讯会议 / 通义听悟 / generic Word |
| `.srt` | SubRip subtitle, time-stamped |
| `.vtt` | WebVTT (honors `<v Speaker>` voice tags) |
| `.json` | OpenAI Whisper / PLAUD / Google STT / Deepgram / generic flat list |

---

## Design principles

These constrain every feature decision:

!!! danger "🟥 No telemetry — ever"
    Not opt-in, not anonymous, not "just for crashes". The project commits to this in [SECURITY.md](https://github.com/Chen17-sq/clearscript/blob/main/SECURITY.md) — if you find a code path that violates it, that's a security issue.

!!! note "🟦 No mandatory network calls"
    Beyond the user's chosen LLM provider. Even local features default to localhost-only.

!!! warning "🟨 No proprietary data formats"
    Markdown, SQLite, JSON — readable from outside clearscript forever. You can move, back up, encrypt, or git-track your data without the application's involvement.

!!! info "⬛ No assumed cloud services"
    Anything that needs an account somewhere is behind a setting that's off by default.

---

## Roadmap

- ✅ **v0.0.7** (current) — Inline editable output + diff view + cost preview + project history + library + 6-format ingest + chunking
- 🚧 **v0.0.8** — Streaming progress (SSE) + project re-run + cross-project search
- 🔮 **v0.1.0** — Mode C cross-chunk learning + privacy redact + domain packs + PyInstaller desktop installers

→ Full plan: [ROADMAP](ROADMAP.md)

---

<p style="text-align: center; margin-top: 3rem;">
  <img src="assets/logo.svg" alt="clearscript logo" width="80" />
</p>
<p style="text-align: center; font-size: 0.85rem; color: var(--bh-ink); opacity: 0.6;">
  <strong>clearscript</strong> · Released under the
  <a href="https://github.com/Chen17-sq/clearscript/blob/main/LICENSE">MIT License</a> ·
  Built for people who care about their transcripts
</p>
