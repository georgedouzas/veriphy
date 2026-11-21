"""The `math` pack's primitives: the Sage daemon, the translation tables, and the composites `meaning` and `certify`.

Importing this package registers the composites.
"""

from veriphy.packs.math.primitives._composites import certify, meaning

__all__ = ['certify', 'meaning']
