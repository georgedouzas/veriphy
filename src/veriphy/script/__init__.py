"""The script API: what a Sage script imports, `from veriphy.script import *`, whichever pack's helpers it uses.

It re-exports the `math` pack's script helpers. Inside a script run by the Sage session they are also bound already.
"""

from veriphy.core._aliases import reexport

reexport(__name__, 'veriphy.packs.math.script')
