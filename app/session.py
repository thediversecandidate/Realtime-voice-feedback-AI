"""Live-call talking-point suggestions from a stream of transcript chunks.

Trigger heuristic, not NLU: a lookup fires once the accumulated buffer
since the last trigger ends in sentence-ending punctuation AND has at
least `min_words` words -- i.e. "wait for a complete, substantial thought,
then look it up." This is a deliberately simple, deterministic rule (easy
to reason about, easy to test) rather than an attempt at real speech
understanding; see CLAUDE.md for what a better trigger would need.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.genesisai_client import RetrievedPassage, query_genesisai

_SENTENCE_ENDERS = (".", "?", "!")


@dataclass(frozen=True)
class Suggestion:
    trigger_text: str
    passages: list[RetrievedPassage]


class LiveSession:
    def __init__(self, query_fn=query_genesisai, min_words: int = 5, limit: int = 2, min_score: float = 5.0):
        self._buffer = ""
        self._min_words = min_words
        self._limit = limit
        self._min_score = min_score
        self._query_fn = query_fn
        self.history: list[Suggestion] = []

    def add_chunk(self, text: str) -> Suggestion | None:
        """Feed the next piece of transcript. Returns a Suggestion if this
        chunk completed a substantial sentence and GenesisAI had a
        passage relevant enough to surface, otherwise None."""
        text = text.strip()
        if not text:
            return None

        self._buffer = f"{self._buffer} {text}".strip() if self._buffer else text

        if not self._buffer.endswith(_SENTENCE_ENDERS):
            return None
        if len(self._buffer.split()) < self._min_words:
            return None

        sentence = self._buffer
        self._buffer = ""

        passages = self._query_fn(sentence, limit=self._limit)
        # FTS5's OR-based matching (see GenesisAI's _sanitize_query) means
        # even filler chatter ("Thanks for joining the call today.") gets
        # *some* weakly-overlapping result back -- observed in practice at
        # bm25 scores around 3, versus ~7-13 for genuinely on-topic
        # questions. min_score filters those false positives out rather
        # than surfacing a suggestion for every sentence spoken.
        passages = [p for p in passages if p.score >= self._min_score]
        if not passages:
            return None

        suggestion = Suggestion(trigger_text=sentence, passages=passages)
        self.history.append(suggestion)
        return suggestion
