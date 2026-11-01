"""Test reasoning runs: the certificate, the checker's verdict, unchecked and rejected runs, and rechecks."""

from collections.abc import Callable
from pathlib import Path

import pytest

from veriphy.graph import builtin_rules, lean_iri, load_graph, load_run, reason, reason_triples, recheck, source_iri, vp

CERTIFICATE_FILES = {'asserted.tsv', 'rules.tsv', 'horn.tsv', 'asserted.sha256', 'run.json', 'check.json'}


def _assumes(node: str, convention: str) -> tuple[str, str, str]:
    """Return an `assumes` triple."""
    return (node, vp('assumes'), convention)


def test_reason_writes_the_certificate(workspace: Path, fake_checker: Callable[[str], Path]) -> None:
    """Write the asserted triples, the rules, the derivations, the digest and the reports."""
    run = reason(load_graph(workspace), fake_checker('accepted'))
    assert run.directory.parent == workspace / '.veriphy' / 'graph' / 'runs'
    assert {p.name for p in run.directory.iterdir()} == CERTIFICATE_FILES
    assert run.complete
    assert run.derived


@pytest.mark.parametrize(
    ('status', 'label', 'checked'),
    [('accepted', 'entailed', True), ('rejected', 'rejected', False), ('unreadable', 'rejected', False)],
)
def test_reason_copies_the_checker_status(
    workspace: Path,
    fake_checker: Callable[[str], Path],
    status: str,
    label: str,
    checked: bool,
) -> None:
    """Report the checker's verdict when it accepts, and no verdict otherwise."""
    run = reason(load_graph(workspace), fake_checker(status))
    assert (run.status, run.label, run.checked) == (status, label, checked)
    assert (run.verdict is not None) == checked


def test_reason_without_a_checker_is_unchecked(workspace: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Label a run unchecked, and name where the checker was looked for and how to build it."""
    monkeypatch.setenv('VERIPHY_OO_HORN', str(workspace / 'missing' / 'oo-horn'))
    run = reason(load_graph(workspace))
    assert (run.status, run.label, run.checked) == ('unchecked_no_checker', 'unchecked', False)
    assert run.report['searched'] == [str(workspace / 'missing' / 'oo-horn')]
    assert 'checker build' in str(run.report['build'])


def test_recheck_compares_the_digest(workspace: Path, fake_checker: Callable[[str], Path]) -> None:
    """Say whether the current graph still asserts the run's triples."""
    graph = load_graph(workspace)
    run = reason(graph, fake_checker('accepted'))
    assert recheck(run.directory, graph, fake_checker('accepted'))[1] is True
    sources = workspace / '.veriphy' / 'graph' / 'sources'
    (sources / 'chapter9.human.ttl').write_text('@prefix vp: <urn:veriphy:vocabulary#> .\n<#eq-4.1> vp:uses <#x> .\n')
    assert recheck(run.directory, load_graph(workspace), fake_checker('accepted'))[1] is False


def test_reason_derives_every_propagation(workspace: Path, checker: Path) -> None:
    """Derive assumes through uses, realizedBy, sameAs and formalizedBy, and caps through formalizedBy, all checked."""
    sources = workspace / '.veriphy' / 'graph' / 'sources'
    (sources / 'extra.human.ttl').write_text(
        '@prefix vp: <urn:veriphy:vocabulary#> .\n@prefix owl: <http://www.w3.org/2002/07/owl#> .\n'
        '<#a> vp:uses <#b> . <#b> vp:uses <#c> . <#c> vp:assumes <#k> .\n'
        '<#f> owl:sameAs <#g> . <#g> vp:assumes <#k2> .\n',
    )
    run = reason(load_graph(workspace), checker)
    a, b, f = (source_iri('extra', x) for x in 'abf')
    k, k2 = source_iri('extra', 'k'), source_iri('extra', 'k2')
    assert run.checked
    assert (run.verdict, run.theorem) == ('entailed', 'OOCert.entails_of_builtin_horn')
    assert all(run.holds(t) for t in (_assumes(a, k), _assumes(b, k), _assumes(f, k2)))
    assert run.holds(_assumes(lean_iri('KK.vacuum'), source_iri('chapter9', 'half')))
    assert run.holds(_assumes(source_iri('chapter9', 'thm-9.1'), source_iri('chapter9', 'half')))
    assert run.holds((source_iri('chapter9', 'thm-9.1'), vp('cappedAt'), vp('oracle-test')))
    builtin = {rule.split('\t')[0] for rule in builtin_rules(checker).splitlines()}
    assert {step.rule for step in run.steps} <= builtin


def test_reason_rejects_a_forged_derivation(workspace: Path, checker: Path) -> None:
    """Reject a run whose derivation line concludes what its premises do not support."""
    run = reason(load_graph(workspace), checker)
    horn = run.directory / 'horn.tsv'
    lines = horn.read_text().splitlines()
    target = next(i for i, line in enumerate(lines) if '#assumes>\t<urn:veriphy:source:chapter9#half>' in line)
    lines[target] = lines[target].replace('chapter9#half>', 'chapter9#one>', 1)
    horn.write_text('\n'.join(lines) + '\n')
    forged, _ = recheck(run.directory, None, checker)
    assert (forged.status, forged.checked) == ('rejected', False)
    assert forged.report.get('ok') is False


def test_reason_triples_reports_an_incomplete_run(tmp_path: Path, fake_checker: Callable[[str], Path]) -> None:
    """Never report a run without a fixpoint as checked."""
    run = reason_triples(
        [(source_iri('ch', 'a'), vp('uses'), source_iri('ch', 'b'))],
        tmp_path,
        fake_checker('accepted'),
    )
    meta = run.directory / 'run.json'
    meta.write_text(meta.read_text().replace('"fixpoint": true', '"fixpoint": false'))
    incomplete = load_run(run.directory)
    assert (incomplete.label, incomplete.checked) == ('incomplete', False)
