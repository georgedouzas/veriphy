"""Test own levels, certified caps, effective levels, and the level report."""

import random
from collections.abc import Callable
from pathlib import Path

import pytest

from veriphy.graph import LevelRow, claim_levels, level_report, load_graph, own_level, reason, source_iri

LEVELS = ('none', 'oracle-test', 'kernel-test', 'certificate')


def _rows(workspace: Path, checker: Path) -> dict[str, LevelRow]:
    """Return the level rows of the fixture workspace by claim label."""
    graph = load_graph(workspace)
    run = reason(graph, checker)
    return {row.claim: row for row in claim_levels(graph, run)}


def test_own_level_comes_from_the_formalization(workspace: Path) -> None:
    """Take a prose claim's own level from the Lean claim that formalizes it, and `none` without one."""
    graph = load_graph(workspace)
    assert own_level(graph, source_iri('chapter9', 'lemma-5.2')) == 'certificate'
    assert own_level(graph, source_iri('chapter9', 'eq-4.1')) == 'none'


def test_claim_levels_caps_a_theorem_on_a_tested_lemma(workspace: Path, fake_checker: Callable[[str], Path]) -> None:
    """Cap a certified theorem at the level of an oracle-tested lemma it uses, and name the lemma."""
    row = _rows(workspace, fake_checker('accepted'))[source_iri('chapter9', 'thm-9.1')]
    assert (row.own, row.effective, row.capped_by) == (
        'certificate',
        'oracle-test',
        source_iri('chapter9', 'lemma-8.4'),
    )
    assert (row.lean_name, row.checked) == ('KK.vacuum', True)


def test_claim_levels_caps_at_a_dependency_without_level(workspace: Path, fake_checker: Callable[[str], Path]) -> None:
    """Cap a claim at `none` when it uses a claim with no level."""
    sources = workspace / '.veriphy' / 'graph' / 'sources'
    (sources / 'chapter9.human.ttl').write_text(
        '@prefix vp: <urn:veriphy:vocabulary#> .\n<#lemma-5.2> vp:uses <#eq-4.1> .\n',
    )
    row = _rows(workspace, fake_checker('accepted'))[source_iri('chapter9', 'lemma-5.2')]
    assert (row.own, row.effective) == ('certificate', 'none')


def test_claim_levels_unchecked_run_keeps_own_levels(workspace: Path, fake_checker: Callable[[str], Path]) -> None:
    """Mark the rows unchecked when the checker rejects the run, and still show the own levels."""
    graph = load_graph(workspace)
    run = reason(graph, fake_checker('rejected'))
    rows = claim_levels(graph, run)
    assert not any(row.checked for row in rows)
    assert 'effective (unchecked)' in level_report(rows, run)


def test_level_report_counts_each_level(workspace: Path, fake_checker: Callable[[str], Path]) -> None:
    """End the report of a source with the number of claims at each effective level."""
    graph = load_graph(workspace)
    run = reason(graph, fake_checker('accepted'))
    report = level_report(claim_levels(graph, run, 'chapter9'), run)
    assert '| thm-9.1 | certificate | oracle-test | lemma-8.4 | KK.vacuum |' in report
    assert report.rstrip().endswith('certificate: 1, kernel-test: 0, oracle-test: 2, none: 2')


def _random_graph(rng: random.Random, size: int) -> tuple[str, dict[int, str], set[tuple[int, int]]]:
    """Return a random source file, its own levels, and its `uses` edges, over claims c0..c(size-1)."""
    levels = {i: rng.choice(LEVELS) for i in range(size) if rng.random() < 0.7}
    edges = {(a, b) for a in range(size) for b in range(size) if a != b and rng.random() < 0.15}
    lines = ['@prefix vp: <urn:veriphy:vocabulary#> .']
    lines += [f'<#c{i}> a vp:Claim ; vp:statedIn <#s> ; vp:statement "c{i}" .' for i in range(size)]
    lines += [f'<#c{i}> vp:hasLevel vp:{level} .' for i, level in levels.items()]
    lines += [f'<#c{a}> vp:uses <#c{b}> .' for a, b in sorted(edges)]
    return '\n'.join(lines) + '\n', levels, edges


def _reachable(start: int, edges: set[tuple[int, int]]) -> set[int]:
    """Return the claims a claim reaches through `uses`, itself included."""
    seen, stack = {start}, [start]
    while stack:
        node = stack.pop()
        for a, b in edges:
            if a == node and b not in seen:
                seen.add(b)
                stack.append(b)
    return seen


@pytest.mark.parametrize('seed', range(5))
def test_claim_levels_never_raise_a_level(tmp_path: Path, fake_checker: Callable[[str], Path], seed: int) -> None:
    """Make each effective level the lowest own level of everything a claim reaches, never higher than its own."""
    rng = random.Random(seed)  # noqa: S311  # nosec B311 - seeded test data, not cryptography
    text, levels, edges = _random_graph(rng, 8)
    (tmp_path / 'lakefile.toml').write_text('')
    sources = tmp_path / '.veriphy' / 'graph' / 'sources'
    sources.mkdir(parents=True)
    (sources / 's.human.ttl').write_text(text)
    graph = load_graph(tmp_path)
    run = reason(graph, fake_checker('accepted'))
    rank = {level: i for i, level in enumerate(LEVELS)}
    for row in claim_levels(graph, run):
        index = int(row.claim.rsplit('#c', 1)[1].rstrip('>'))
        expected = min((levels.get(i, 'none') for i in _reachable(index, edges)), key=rank.__getitem__)
        assert row.effective == expected
        assert rank[row.effective] <= rank[row.own]
