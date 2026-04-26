# X / Twitter launch thread

Eight tweets. Designed to be readable as a thread or excerptable as standalone tweets. Numbers indicate position; the URL goes in tweet 1 and tweet 8.

---

**1/**

I do a lot of interviews — VC reference calls, founder chats, customer research.

Every single one ends with a 90-minute ASR transcript that's 95% right.

The last 5% is where 45 minutes of my life goes. Same speaker labels, same misheard names, every single time.

So I built this:

🔗 https://github.com/Chen17-sq/clearscript

---

**2/**

clearscript is a local-first transcript editor that **remembers what you fix**.

Drop in raw ASR (.docx, .srt, .txt, .json — every format) → pick any model → click Run → edit inline → download .docx.

Your fixes go into a SQLite library. Run #10 barely needs touching.

---

**3/**

The differentiator isn't the cleanup. It's the memory.

A blank-slate LLM is dumb every time. It doesn't know "Speaker 2" was Eileen last week. It doesn't know your ASR tool keeps mishearing "Dify" as "DeFi".

clearscript builds your private knowledge base. The library is the product.

---

**4/**

Why local-first?

I do confidential ref checks. Cloud SaaS can't see them.

I want to switch models freely — Claude when quality matters, DeepSeek when cost matters, Ollama when I can't send anything. Same workflow.

My library is institutional memory. It belongs on my laptop.

---

**5/**

What's in the box (v0.0.7):

→ Bauhaus-styled local web UI
→ Inline editable output with diff highlighting
→ Live cost preview ($0.03 / 90-min interview with DeepSeek)
→ Library tab: terms / speakers / edit patterns
→ Project history: every run saved, browsable, re-downloadable
→ 6 input formats, 5 provider adapters (20+ services)

---

**6/**

The library compounds.

After a few sessions:
• Auto-detected speakers get pre-labeled with their real names
• Misheard company names get caught in the prompt
• Your "do not change" rules persist
• Mode B suggests new entries after every run; one click to accept

---

**7/**

It also ships as a Claude skill.

If you use Claude Code or the Agent SDK, you can drop `clearscript.skill` into `~/.claude/skills/` and your agent gets the same 7-layer transcript-cleanup pipeline.

Same prompts as the standalone app. Single source of truth.

---

**8/**

Built with Python + uv + SQLite + a Bauhaus-styled SPA in pure HTML/Tailwind/JS. ~10k LOC. MIT licensed.

It's the kind of tool I always wished someone had made. So I made it. For free.

Code: https://github.com/Chen17-sq/clearscript
Site: https://chen17-sq.github.io/clearscript/
