"""HTTP client for the GenesisAI knowledge-retrieval API.

Realtime-voice-feedback-AI is a thin client, not a fork of GenesisAI's
retrieval logic -- see GenesisAI's CLAUDE.md. This module is the only
place that talks to it over HTTP. (Deliberately a separate copy from
EmailAnalysis's identical-looking client rather than a shared package --
these are independent thin services, each hitting GenesisAI over HTTP,
not a shared codebase; see CLAUDE.md.)
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import requests

GENESISAI_URL = os.environ.get("GENESISAI_URL", "http://localhost:8000")


@dataclass(frozen=True)
class RetrievedPassage:
    source_file: str
    breadcrumb: str
    heading: str
    text: str
    score: float


class GenesisAIError(RuntimeError):
    """Raised when GenesisAI is unreachable or returns an error."""


def query_genesisai(question: str, limit: int = 2, base_url: str = GENESISAI_URL) -> list[RetrievedPassage]:
    try:
        resp = requests.post(
            f"{base_url}/query",
            json={"question": question, "limit": limit},
            timeout=10,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise GenesisAIError(f"GenesisAI request failed: {exc}") from exc

    data = resp.json()
    return [RetrievedPassage(**r) for r in data["results"]]
