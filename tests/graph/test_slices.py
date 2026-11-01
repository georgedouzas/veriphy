"""Test claim slices: their premises, the check that they keep consequences, and their rendering."""

from collections.abc import Callable
from pathlib import Path

from veriphy.graph import check_slice, load_graph, reason, render_slice, slice_claim, slice_premises, source_iri, vp

THM, LEMMA = source_iri('chapter9', 'thm-9.1'), source_iri('chapter9', 'lemma-5.2')


def test_slice_premises_keep_only_what_the_claim_rests_on(workspace: Path, fake_checker: Callable[[str], Path]) -> None:
    """Hold the claim's and its dependencies' assertions, and nothing about unrelated claims."""
    graph = load_graph(workspace)
    premises = slice_premises(reason(graph, fake_checker('accepted')), THM)
    subjects = {s for s, _, _ in premises}
    assert (LEMMA, vp('assumes'), source_iri('chapter9', 'half')) in premises
    assert source_iri('chapter9', 'eq-4.1') not in subjects
    assert source_iri('arXiv:0808.3236', 'thm-2') not in subjects


def test_slice_claim_keeps_every_consequence(workspace: Path, checker: Path) -> None:
    """Derive from the slice alone every consequence about the claim, by two checked runs."""
    graph = load_graph(workspace)
    piece = slice_claim(graph, reason(graph, checker), THM, checker)
    assert piece.keeps
    assert piece.own.verdict == 'entailed'


def test_slice_claim_reports_lost_consequences(workspace: Path, fake_checker: Callable[[str], Path]) -> None:
    """List the consequences a slice without a premise loses."""
    graph = load_graph(workspace)
    run = reason(graph, fake_checker('accepted'))
    trimmed = slice_premises(run, THM) - {(THM, vp('uses'), LEMMA)}
    piece = check_slice(graph, run, THM, trimmed, fake_checker('accepted'))
    assert (THM, vp('assumes'), source_iri('chapter9', 'half')) in piece.lost
    assert not piece.keeps


def test_render_slice_names_conventions_and_lean(workspace: Path, fake_checker: Callable[[str], Path]) -> None:
    """Render statements, conventions with their aspects and Lean realizations, and levels."""
    graph = load_graph(workspace)
    run = reason(graph, fake_checker('accepted'))
    text = render_slice(graph, slice_claim(graph, run, THM, fake_checker('accepted')))
    assert text.startswith('# Context for thm-9.1\n\nThe vacuum is stable.')
    assert '- lemma-5.2 [certificate]: The Killing form.' in text
    assert '- half (killing-normalization): Tr(TT) = 1/2 — Lean: KK.half' in text
    assert 'Level: own certificate, effective oracle-test (checked), Lean: KK.vacuum' in text
