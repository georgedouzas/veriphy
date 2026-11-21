"""Digest content and render values as canonical JSON, the same way everywhere in Veriphy."""

import hashlib
import json


def canonical_json(value: object) -> str:
    """Return the canonical JSON text of a value: sorted keys, no spaces, UTF-8 kept.

    Args:
        value: A JSON-serializable value.

    Returns:
        The text that the same value always gives.

    Examples:
        >>> canonical_json({'b': 1, 'a': [2, 'é']})
        '{"a":[2,"é"],"b":1}'
    """
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def content_digest(content: str | bytes) -> str:
    """Return the SHA-256 of a text or a byte string, in hexadecimal.

    Args:
        content: The content.

    Returns:
        The digest.

    Examples:
        >>> content_digest('abc') == content_digest(b'abc')
        True
    """
    data = content.encode() if isinstance(content, str) else content
    return hashlib.sha256(data).hexdigest()
