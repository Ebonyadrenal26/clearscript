# Known speakers

Speakers who appear repeatedly in your transcripts, with the canonical label format and the ASR mis-transcriptions seen in the wild.

**How the skill uses this:** read this file at the start of every session. When you see a speaker label in the raw transcript, check this list. If you find a match, normalize to the canonical label immediately. If a speaker is new, leave them with their best-guess real name and add them to the SUGGESTIONS block at the end.

## Format

| Real identity | Canonical label | ASR variants seen |
|---|---|---|
| _example placeholder_ | `_name_:` | `Speaker N`, ... |

Add rows below as you confirm corrections.

## Anonymized fallback

When the speaker shouldn't be named in the deliverable, use:

- English / international context: `Interviewee:`
- Chinese context: `受访者：`

Never use `Speaker N` or job-title-as-label in the final output.
