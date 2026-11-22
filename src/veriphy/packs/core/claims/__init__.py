"""Register the framework's steps over the claim graph: `validate`, `reason`, `appendix` and `check-concepts`."""

from veriphy.claims import APPENDIX, REASON, VALIDATE
from veriphy.packs.core.claims._concepts import CHECK_CONCEPTS
from veriphy.steps import register

register(VALIDATE, REASON, APPENDIX, CHECK_CONCEPTS, pack='core')
