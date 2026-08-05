from app.genesisai_client import RetrievedPassage
from app.session import LiveSession, Suggestion


def _fake_passages():
    return [RetrievedPassage("workbook.md", "b", "h", "Relevant fact.", 5.0)]


def test_no_trigger_until_sentence_terminated():
    session = LiveSession(query_fn=lambda q, limit: _fake_passages())
    assert session.add_chunk("What standard") is None
    assert session.add_chunk("governs hi-pot") is None
    result = session.add_chunk("testing?")
    assert result is not None
    assert result.trigger_text == "What standard governs hi-pot testing?"


def test_no_trigger_for_sentence_below_min_word_count():
    session = LiveSession(query_fn=lambda q, limit: _fake_passages(), min_words=5)
    assert session.add_chunk("Okay.") is None  # 1 word, below threshold
    # Buffer isn't cleared -- accumulates into the next sentence instead.
    result = session.add_chunk("What voltage class is this switchgear?")
    assert result is not None
    assert result.trigger_text == "Okay. What voltage class is this switchgear?"


def test_returns_none_and_clears_buffer_when_no_passages_found():
    session = LiveSession(query_fn=lambda q, limit: [])
    result = session.add_chunk("A completely unrelated sentence about lunch plans.")
    assert result is None
    # Buffer should have been cleared even though nothing was returned --
    # otherwise unrelated filler would keep getting glued onto the next
    # real question forever.
    assert session._buffer == ""


def test_history_only_records_successful_suggestions():
    session = LiveSession(query_fn=lambda q, limit: _fake_passages())
    session.add_chunk("What standard governs hi-pot testing?")
    assert len(session.history) == 1
    assert isinstance(session.history[0], Suggestion)


def test_add_chunk_ignores_empty_lines():
    session = LiveSession(query_fn=lambda q, limit: _fake_passages())
    assert session.add_chunk("") is None
    assert session.add_chunk("   \n") is None


def test_filters_out_low_relevance_passages():
    # Regression: FTS5's OR-based matching means even filler chatter gets
    # *some* weakly-related result back. A passage below min_score
    # shouldn't produce a suggestion.
    weak = [RetrievedPassage("workbook.md", "b", "h", "Weakly related.", 3.0)]
    session = LiveSession(query_fn=lambda q, limit: weak, min_score=5.0)
    result = session.add_chunk("Thanks for joining the call today.")
    assert result is None
    assert session.history == []


def test_keeps_passages_at_or_above_min_score():
    mixed = [
        RetrievedPassage("workbook.md", "b1", "h1", "Strong match.", 8.0),
        RetrievedPassage("workbook.md", "b2", "h2", "Weak match.", 2.0),
    ]
    session = LiveSession(query_fn=lambda q, limit: mixed, min_score=5.0)
    result = session.add_chunk("What standard governs hi-pot testing?")
    assert result is not None
    assert len(result.passages) == 1
    assert result.passages[0].text == "Strong match."


def test_query_fn_receives_the_configured_limit():
    received = {}

    def fake_query(question, limit):
        received["limit"] = limit
        return _fake_passages()

    session = LiveSession(query_fn=fake_query, limit=3)
    session.add_chunk("What standard governs hi-pot testing?")
    assert received["limit"] == 3
