"""Feed a transcript file through LiveSession, line by line, printing
suggestions as they'd surface during a real call.

This reads pre-written text from a file -- it does NOT capture audio or
call a speech-to-text service. See CLAUDE.md for what real-time audio
input would actually require.
"""

import sys

from app.genesisai_client import GenesisAIError
from app.session import LiveSession


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python -m app.cli <transcript-file>", file=sys.stderr)
        print("(each line is fed in as one incoming transcript chunk)", file=sys.stderr)
        sys.exit(1)

    session = LiveSession()

    try:
        with open(sys.argv[1]) as f:
            for line in f:
                suggestion = session.add_chunk(line)
                if suggestion is None:
                    continue
                print(f'\n[heard]: "{suggestion.trigger_text}"')
                for p in suggestion.passages:
                    snippet = p.text.strip().replace("\n", " ")
                    if len(snippet) > 200:
                        snippet = snippet[:200].rstrip() + "..."
                    print(f"  -> {p.breadcrumb} ({p.source_file})")
                    print(f'     "{snippet}"')
    except GenesisAIError as exc:
        print(f"Error: {exc}\nIs GenesisAI running (GENESISAI_URL, default http://localhost:8000)?", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
