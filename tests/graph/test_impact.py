"""Test the impact of a convention and plans of a graph edit against a git revision."""

from collections.abc import Callable
from pathlib import Path

from veriphy.graph import convention_impact, impact_report, load_graph, plan, plan_report, reason, source_iri, vp

HALF, ONE = source_iri('chapter9', 'half'), source_iri('chapter9', 'one')


def test_convention_impact_lists_direct_and_transitive_nodes(
    workspace: Path,
    fake_checker: Callable[[str], Path],
) -> None:
    """List the claim that states the convention with no chain, and a claim that reaches it with its chain."""
    graph = load_graph(workspace)
    run = reason(graph, fake_checker('accepted'))
    entries = {e.node: e for e in convention_impact(graph, run, HALF)}
    lemma, eq = source_iri('chapter9', 'lemma-5.2'), source_iri('chapter9', 'eq-7.3')
    assert entries[lemma].chain == (lemma,)
    assert entries[eq].chain == (eq, lemma)
    assert '- eq-7.3 via lemma-5.2' in impact_report(tuple(entries.values()), run, HALF)


def test_convention_impact_marks_formalized_claims(workspace: Path, fake_checker: Callable[[str], Path]) -> None:
    """Show the Lean name and level of an affected claim, and reach Lean claims through a realizing definition."""
    graph = load_graph(workspace)
    run = reason(graph, fake_checker('accepted'))
    entries = {e.node: e for e in convention_impact(graph, run, HALF)}
    assert (
        entries[source_iri('chapter9', 'lemma-5.2')].lean_name,
        entries[source_iri('chapter9', 'lemma-5.2')].level,
    ) == (
        'KK.killing_form_value',
        'certificate',
    )
    assert '<urn:veriphy:lean:KK.vacuum>' in entries


def test_impact_report_unchecked(workspace: Path, fake_checker: Callable[[str], Path]) -> None:
    """Print the impact under the word unchecked when the checker did not accept the run."""
    graph = load_graph(workspace)
    run = reason(graph, fake_checker('rejected'))
    assert '(run ' in impact_report(convention_impact(graph, run, HALF), run, HALF)
    assert 'rejected' in impact_report(convention_impact(graph, run, HALF), run, HALF)


def test_plan_lists_a_switched_convention(committed: Path, fake_checker: Callable[[str], Path]) -> None:
    """List the claims that lose one convention and gain another, and the clash the edit creates."""
    workspace = committed
    sources = workspace / '.veriphy' / 'graph' / 'sources'
    text = (sources / 'chapter9.agent.ttl').read_text().replace('vp:assumes :half', 'vp:assumes :one')
    (sources / 'chapter9.agent.ttl').write_text(text)
    result = plan(load_graph(workspace), 'HEAD', fake_checker('accepted'))
    eq = source_iri('chapter9', 'eq-7.3')
    assert (eq, vp('assumes'), HALF) in result.removed
    assert (eq, vp('assumes'), ONE) in result.added
    assert result.checked
    assert '+ eq-7.3 assumes one' in plan_report(result)


def test_plan_reports_a_statement_edit_without_consequences(
    committed: Path,
    fake_checker: Callable[[str], Path],
) -> None:
    """Report one changed assertion and no changed consequence for a statement edit."""
    workspace = committed
    sources = workspace / '.veriphy' / 'graph' / 'sources'
    text = (sources / 'chapter9.agent.ttl').read_text().replace('"An estimate."', '"A sharper estimate."')
    (sources / 'chapter9.agent.ttl').write_text(text)
    result = plan(load_graph(workspace), 'HEAD', fake_checker('accepted'))
    assert (len(result.assertions_added), len(result.assertions_removed)) == (1, 1)
    assert not result.added
    assert not result.removed
    assert '0 changed consequences (checked)' in plan_report(result)
