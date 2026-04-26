# Show HN post

Title: **Show HN: Clearscript – a local-first transcript editor that learns your jargon**

(HN titles cap at 80 chars. The above is 76. Avoid emoji, ALL-CAPS, and the word "AI" at the front; both kill submissions.)

---

I do a lot of interviews — VC reference calls, founder chats, customer research, the occasional podcast. Every single one comes back from my ASR tool 95% right and 5% mind-numbing: "Speaker 2" never gets a real name, "Dify" gets transcribed as "DeFi", "PingCAP" as "PinkCup", the mic-check pleasantries are still in there, and I delete the same hallucinated AI summary block every time.

I'd been hand-fixing this for years. Last fall I built a personal Claude skill to handle the cleanup. After running it on ~200 transcripts I open-sourced the result.

It's organized around three opinions:

**1. Local-first by architecture, not by checkbox.** Transcripts and the terminology library never leave your disk. The only network call is the one you authorize: your chosen LLM. No telemetry, no accounts, no analytics. You can `rm -rf` the install and lose nothing important; you can `git init` the library and version-control your knowledge.

**2. Memory compounds.** A blank-slate LLM is dumb every time. clearscript builds a SQLite knowledge base of speakers, terms, edit patterns, and "do not change" rules. Mode A pre-loads relevant entries before each run; Mode B harvests new ones after. By the 10th transcript on a given project, the model barely makes corrections — they're already in the library.

**3. Bring your own model.** Five adapters cover 20+ services: Anthropic, OpenAI, OpenAI-compat (DeepSeek/Moonshot/Qwen/Together/Groq/Fireworks/Mistral/OpenRouter/Kimi/Zhipu/MiniMax/etc.), Google, Ollama, llama.cpp, LM Studio, custom endpoints. Same workflow. Costs ~$0.03 per 90-min interview with DeepSeek, ~$0.20 with Claude Sonnet, free with Ollama.

The editing pipeline is structured as 7 named layers (speaker normalization → trim → ASR fix → sentence reconstruction → information preservation → format → punctuation). Every change is logged with reason and confidence; the UI has a "Diff" view that highlights changes by layer with hover-tooltips for why each was made. Inline editable output auto-saves to the project file. Long transcripts auto-chunk so 90+ minute interviews don't crash.

Stack: Python 3.11+, uv, SQLite (FTS5), a single-page web UI built with vanilla JS + Tailwind via CDN + Bauhaus-styled CSS. FastAPI backend serving localhost only. ~10k LOC, 97 tests, CI on macOS/Linux/Windows × Py 3.11/3.12/3.13.

Also ships as a Claude skill: drop `clearscript.skill` into `~/.claude/skills/` and your agent picks up the same 7-layer pipeline. Single source of truth — both the app and the skill load prompts from the same markdown files.

Repo: https://github.com/Chen17-sq/clearscript
Live docs: https://chen17-sq.github.io/clearscript/

Happy to answer questions about the architecture, the prompt library design, or the local-first decisions.

---

# Reply templates for common HN questions

**"Why not just use Whisper / paste into ChatGPT?"**

Whisper transcribes audio; clearscript edits transcripts. They compose: feed Whisper output to clearscript. ChatGPT works for one-off cleanup but has no memory across sessions — every time you start over with the same misheard names. clearscript's whole value proposition is the library that learns.

**"Why local instead of a hosted version?"**

Two reasons. Privacy: I do confidential ref checks where uploading to anyone's cloud isn't an option. Lock-in: a hosted clearscript would need to pick a model provider; local clearscript lets you change provider in a single config line.

**"What about long transcripts?"**

Auto-chunking at speaker-turn boundaries with a default 3500-token target. A 90-minute interview becomes ~8-12 chunks; outputs are stitched and the library state is shared across chunks. v0.0.8 will add cross-chunk learning so chunk N's confirmations feed chunk N+1's prompt.

**"How accurate is the cleanup?"**

Depends entirely on which model you pick. Claude Opus ~99% on a clean library. DeepSeek-chat ~95-97%. Ollama qwen2.5:14b ~85-90% but free and fully local. The diff view exists so you trust it: every change is highlighted and explained.

**"Mac/Linux/Windows?"**

All three. PyInstaller-packaged single-binary installers are scheduled for v0.1.

**"Why Bauhaus design?"**

The original skill was a personal tool with no UI. Open-sourcing meant making it presentable. I picked Bauhaus because it's geometrically honest — every color, border, and shadow has a function — which fit the project's "no decorative cruft" ethos. Three primaries (red/blue/yellow) maps cleanly to the three core ideas (local-first / BYOM / library).
