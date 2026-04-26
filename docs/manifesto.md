# The clearscript way

Four beliefs, in order of importance. Every feature in this repo is downstream of one of them. Anything that contradicts them won't ship.

---

## 1. Your transcripts aren't training data.

People talk to you in confidence. Founders, candidates, customers, patients, sources.

When you upload that conversation to a cloud SaaS, you're sharing a private moment with a vendor's storage tier, their analytics pipeline, and — eventually — their next model release. The "we delete it after 30 days" promise is a checkbox, not an architecture.

clearscript runs on your machine. The transcript file lives in `~/Documents/clearscript/projects/`. The terminology library lives in `~/.local/share/clearscript/library/`. The only network call is the one you authorize: a request to whichever LLM you picked, with the text you chose to send. No background sync. No telemetry. No "anonymous usage data". No account.

You can `rm -rf` the whole thing and you're done. You can `tar czf` the whole thing and back it up. You can `git init` your library and version it. None of that requires our permission, because the data was never ours.

---

## 2. ASR is a starting point, not a deliverable.

There's a whole industry selling you transcription. Otter, Rev, Sonix, AssemblyAI, every meeting recorder. They all stop the same place: at 95% accuracy, with no idea who's talking and a lot of "Speaker 2".

That last 5% is where the actual work is. The names, the jargon, the cleanup, the formatting, the speaker labeling. clearscript starts where Whisper stops.

We don't transcribe audio. We make the transcript usable.

---

## 3. Memory is the moat.

A blank-slate LLM is dumb every time you talk to it. It doesn't know that "Eileen" was "Speaker 2" last week. It doesn't know "Dify" sounds like "DeFi" to your particular ASR tool. It doesn't know you prefer to keep the speaker's "差不多三四百人" instead of standardizing it to "约 350".

Every other tool throws this knowledge away after each session.

clearscript builds it up. Speakers, terms, edit patterns, "do not change" rules — all stored in a SQLite library on your disk, growing every time you accept a correction. By the tenth interview your fixes are mostly already in place before you click Run.

The library is the product. The model is just a fungible engine.

---

## 4. Bring your own model.

You should be able to:

- Use Claude Opus when you care about quality
- Use DeepSeek when you care about cost (~$0.03 per 90-min interview)
- Use Ollama when you can't send anything to the cloud at all
- Switch between them mid-project, in a config file, with no other change

Closed-API tools that lock you to one provider are bets on that provider's pricing, performance, and continued existence. clearscript is built on a five-line provider abstraction: Anthropic, OpenAI, OpenAI-compat (covers DeepSeek/Moonshot/Qwen/Together/Groq/Fireworks/Mistral/OpenRouter/Kimi/Zhipu/MiniMax/etc.), Google, Ollama. Twenty-plus services, one workflow.

When the next model comes out, you'll add a single line of config and use it. When today's leader gets disrupted, you'll forget about them. The workflow stays.

---

## What this means in practice

| You won't see this in clearscript | Because of |
|---|---|
| "Sign in with Google" | #1 |
| "Anonymized usage data helps us improve" | #1 |
| Recommended cloud providers | #1, #4 |
| "Premium" tier with extra features | #4 |
| Speaker recognition without your input | #3 |
| Closed prompt library you can't read or modify | #1 |
| Auto-summarization "for your convenience" | #2 |
| One-click sharing to a hosted gallery | #1 |

You will see: a SQLite file, some markdown, a config.toml, and source code under MIT.

That's the whole product.
