"""The `math` pack's primitives: the Sage session, the translation tables, and the composites `sample` and `certify`.

Importing this package registers the composites.
"""

from veriphy.packs.math.primitives._composites import certify, sample

__all__ = ['certify', 'sample']
