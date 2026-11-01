"""Test SHACL shapes, proposed `excludes` triples, and clashes."""

from collections.abc import Callable
from pathlib import Path

from veriphy.graph import (
    add_triples,
    clash_report,
    clashes,
    load_graph,
    propose_excludes,
    reason,
    shape_report,
    source_iri,
    validate_shapes,
    vp,
)

HALF, ONE = source_iri('chapter9', 'half'), source_iri('chapter9', 'one')
SOURCES = Path('.veriphy') / 'graph' / 'sources'


def _write(workspace: Path, text: str) -> None:
    """Add a human source file to the workspace."""
    (workspace / SOURCES / 'chapter3.human.ttl').write_text('@prefix vp: <urn:veriphy:vocabulary#> .\n' + text)


def test_validate_shapes_accepts_the_fixture(workspace: Path) -> None:
    """Report a conforming graph as the validator's measurement, not as checked."""
    report = validate_shapes(load_graph(workspace))
    assert report.conforms
    assert 'a measurement, not a check' in shape_report(report)


def test_validate_shapes_reports_a_claim_without_statement(workspace: Path) -> None:
    """Report the claim, the shape's message and the file."""
    _write(workspace, '<#eq-3.4> a vp:Claim ; vp:statedIn <#chapter3> .\n')
    report = validate_shapes(load_graph(workspace))
    (violation,) = report.violations
    assert violation.focus == source_iri('chapter3', 'eq-3.4')
    assert violation.message == 'a claim needs a statement'
    assert violation.files[0].name == 'chapter3.human.ttl'


def test_validate_shapes_reports_broken_lean_links(workspace: Path) -> None:
    """Report a formalizedBy or realizedBy link to a Lean name the export does not hold."""
    _write(
        workspace,
        '<#eq-3.12> a vp:Claim ; vp:statedIn <#c> ; vp:statement "x" ; vp:formalizedBy <urn:veriphy:lean:KK.gone> .\n'
        '<#sig> a vp:Convention ; vp:conventionFor "metric" ; vp:realizedBy <urn:veriphy:lean:KK.gone> .\n',
    )
    messages = {v.message for v in validate_shapes(load_graph(workspace)).violations}
    assert any('formalizedBy' in m for m in messages)
    assert any('realizedBy' in m for m in messages)


def test_propose_excludes_pairs_conventions_of_one_aspect(workspace: Path) -> None:
    """Propose one triple for two conventions of the same aspect, and nothing once it is asserted."""
    graph = load_graph(workspace)
    assert propose_excludes(graph) == ((HALF, vp('excludes'), ONE),)
    add_triples(workspace, 'chapter9', 'human', {(HALF, vp('excludes'), ONE)})
    assert propose_excludes(load_graph(workspace)) == ()


def test_clashes_reports_a_clash_across_papers(workspace: Path, checker: Path) -> None:
    """Report a claim that inherits two exclusive conventions from two papers, with the checker's verdict."""
    add_triples(workspace, 'chapter9', 'human', {(HALF, vp('excludes'), ONE)})
    _write(
        workspace,
        '<#thm-9.9> a vp:Claim ; vp:statedIn <#c> ; vp:statement "x" ; '
        'vp:uses <urn:veriphy:source:chapter9#lemma-5.2>, <urn:veriphy:source:arXiv:0808.3236#thm-2> .\n',
    )
    graph = load_graph(workspace)
    run = reason(graph, checker)
    found = clashes(graph, run)
    node = source_iri('chapter3', 'thm-9.9')
    assert [(c.node, c.first, c.second, c.checked) for c in found] == [(node, HALF, ONE, True)]
    assert 'thm-9.9 assumes half and one' in clash_report(found, run)


def test_clash_report_says_absence_is_not_checked(workspace: Path, fake_checker: Callable[[str], Path]) -> None:
    """Say that no clash is the reasoner's result, not a checked conclusion."""
    graph = load_graph(workspace)
    run = reason(graph, fake_checker('accepted'))
    assert clashes(graph, run) == ()
    assert 'not a checked conclusion' in clash_report((), run)
