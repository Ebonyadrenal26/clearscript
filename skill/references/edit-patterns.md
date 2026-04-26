# Edit patterns

User preferences sedimented from past transcript-editing sessions. The base rules are in `prompts/layers/l*.md` — this file is for **deltas and edge cases** that came up after the user pushed back on something.

**How the skill uses this:** read this file at the start of every session, after `speakers.md` and `asr-corrections.md`. Apply these patterns silently. They override conflicting defaults.

**How to add:** at the end of every run, the SUGGESTIONS block proposes new patterns when the user actively corrects you ("don't summarize like this", "keep this phrase intact", "this kind of stutter doesn't need fixing"). When the user accepts a suggestion, append it below.

## Format for each entry

```
### [Short title]

**Trigger:** [when this situation occurs in a transcript]
**Action:** [what to do — concrete, imperative]
**Source:** [project name / session date / accepting user feedback]
**Why:** [the reasoning the user gave, if any]
```

## Patterns

_(empty — populates as the user accepts SUGGESTIONS)_
