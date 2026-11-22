"""Register the claim graph's steps, `validate`, `reason` and `appendix`, which `veriphy.claims` defines."""

from veriphy.claims import APPENDIX, REASON, VALIDATE
from veriphy.steps import register

register(VALIDATE, REASON, APPENDIX, pack='core')
