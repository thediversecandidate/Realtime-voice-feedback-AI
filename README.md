# Realtime-voice-feedback-AI

A thin client for `GenesisAI`: feeds a stream of live-call transcript
chunks in, surfaces cited talking points out. See `CLAUDE.md` for how this
fits with `GenesisAI` and `EmailAnalysis`.

## Quick start

```bash
pip install -e ".[dev]"
pytest -q
# with a GenesisAI instance running (default http://localhost:8000):
python -m app.cli path/to/transcript.txt   # one line per transcript chunk
```

Not live audio capture or speech-to-text — see `CLAUDE.md`.
