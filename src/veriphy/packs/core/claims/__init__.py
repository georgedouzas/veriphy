"""Register the claim graph's steps, `validate`, `reason` and `report`, which `veriphy.claims` defines."""

from veriphy.claims import REASON, REPORT, VALIDATE
from veriphy.steps import register

register(VALIDATE, REASON, REPORT)
