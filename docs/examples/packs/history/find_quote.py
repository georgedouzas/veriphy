"""Find a passage in a source text, ignoring line breaks and runs of spaces, and write the result as JSON."""

import json
import sys
from pathlib import Path


def main() -> None:
    """Read the input file named first, and write `found` with the line, or `missing`, to the file named second."""
    inputs = json.loads(Path(sys.argv[1]).read_text())
    words = ' '.join(str(inputs['passage']).split())
    text = Path(inputs['source']).read_text()
    joined = ' '.join(text.split())
    position = joined.find(words)
    if position < 0:
        result = {'status': 'missing'}
    else:
        # the line of the source where the passage starts
        prefix = joined[:position].split()
        line = text[: sum(len(w) for w in prefix)].count('\n') + 1 if prefix else 1
        result = {'status': 'found', 'line': line}
    Path(sys.argv[2]).write_text(json.dumps(result))


if __name__ == '__main__':
    main()
