# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A thin client for `GenesisAI`'s knowledge retrieval API. This repo,
`GenesisAI`, and `EmailAnalysis` used to be three empty placeholder repos;
they're now one consolidated tool (GenesisAI's knowledge base + query API)
with two input/output modalities. **Do not rebuild retrieval or
knowledge-base logic here** — see `GenesisAI`'s CLAUDE.md for why and for
the architecture this repo depends on.

## What this does

`app/session.py`'s `LiveSession` takes a stream of transcript chunks
(`add_chunk(text)`) and decides when to surface a `Suggestion` (cited
passages from GenesisAI):

1. Accumulate chunks into a buffer until it ends in `.`/`?`/`!` **and**
   has at least `min_words` (default 5) — "wait for a complete,
   substantial thought, then look it up." A short "complete" sentence
   below the word threshold doesn't reset the buffer; it glues onto the
   next sentence instead (see `tests/test_session.py`'s
   `test_no_trigger_for_sentence_below_min_word_count` for the exact
   behavior).
2. Query GenesisAI with the accumulated sentence.
3. **Filter results below `min_score`** (default 5.0) before surfacing a
   suggestion. This exists because GenesisAI's FTS5 matching is OR-based
   (see its `_sanitize_query`) — even filler chatter like "Thanks for
   joining the call today." gets *some* weakly-overlapping result back.
   Measured in practice: filler scores land around 3, genuinely on-topic
   questions score 7-13+. Without this filter, the tool would "suggest"
   something after every sentence spoken, which defeats the point.

`app/cli.py` drives a `LiveSession` from a text file, one line per
transcript chunk, printing suggestions as they'd surface live.

Verified end-to-end (2026-08) against a live local GenesisAI instance with
a simulated call transcript: filler ("Thanks for joining the call today.")
correctly produced no suggestion; "What standard governs hi-pot testing
for medium voltage switchgear?" and "What is the acceptance criteria for
insulation resistance testing on new switchgear installations?" both
surfaced the correct, specific workbook sections (including landing
exactly on "5.1 IEEE 43-2013 — Insulation Resistance Testing" for the
second question).

## What this deliberately does NOT do yet

**No live audio capture or speech-to-text.** `LiveSession.add_chunk()`
takes plain text; nothing here touches a microphone or calls an STT
service. `app/cli.py` reads pre-written lines from a file specifically so
this can be tested and demoed without pretending to have a live-audio
integration that doesn't exist. Wiring real-time audio in means: picking
an STT provider (with real API credentials the user supplies), deciding
how partial/streaming transcripts map onto `add_chunk()`'s
one-chunk-at-a-time model (a real STT stream doesn't arrive as neat
sentences), and almost certainly tuning `min_words`/`min_score` against
real call audio rather than the clean, typed test transcript used here.
Don't fake microphone input to make this look more finished than it is.

## Testing

```bash
pip install -e ".[dev]"
pytest -q
```

`tests/test_genesisai_client.py` mocks `requests.post`; `test_session.py`
uses a fake `query_fn` — no test here requires a running GenesisAI
instance. For a real end-to-end check, run GenesisAI locally
(`make run` in that repo) and use `app/cli.py` with a sample transcript
file against it directly.
