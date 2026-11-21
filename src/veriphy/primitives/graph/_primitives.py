"""The `core` pack's primitives as Python functions: `horn.check` (the verified checker) and `shacl.validate`."""

from pathlib import Path

from veriphy.primitives.graph._checker import PINNED_RELEASE, check_certificate, ensure_checker
from veriphy.primitives.graph._engine import parse_rdf, validate_shacl


def horn_check(inputs: dict[str, object]) -> dict[str, object]:
    """Have `oo-horn`, the pinned release set up on first use, check a certificate directory.

    Args:
        inputs: `certificate`, the directory holding `rules.tsv`, `asserted.tsv` and `horn.tsv`.

    Returns:
        The checker's report with its status, and `oo-horn` among its tools with its pinned commit.
    """
    report = check_certificate(Path(str(inputs['certificate'])), ensure_checker())
    return {**report, 'tools': [{'name': 'oo-horn', 'version': PINNED_RELEASE.commit, 'pin': 'commit'}]}


def shacl_validate(inputs: dict[str, object]) -> dict[str, object]:
    """Validate a graph against shapes; validation is a measurement, and grants nothing.

    Args:
        inputs: `data`, an N-Triples file, and `shapes`, a Turtle file.

    Returns:
        Whether the data conforms, and each violation's focus node, path and message.
    """
    data = parse_rdf(Path(str(inputs['data'])).read_text(), 'ntriples')
    violations = validate_shacl(data, Path(str(inputs['shapes'])).read_text())
    return {'conforms': not violations, 'violations': violations}
