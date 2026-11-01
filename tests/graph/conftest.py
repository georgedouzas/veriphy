"""Provide the research-graph fixtures: a workspace with sources and a Lean export, and real or fake checkers."""

import json
import os
import shutil
import stat
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

from veriphy.graph import find_checker

PREFIXES = '@prefix vp: <urn:veriphy:vocabulary#> .\n@prefix owl: <http://www.w3.org/2002/07/owl#> .\n'
CHAPTER = """@prefix : <urn:veriphy:source:chapter9#> .
:half a vp:Convention ; vp:conventionFor "killing-normalization" ; vp:statement "Tr(TT) = 1/2" ;
    vp:realizedBy <urn:veriphy:lean:KK.half> .
:one a vp:Convention ; vp:conventionFor "killing-normalization" ; vp:statement "Tr(TT) = 1" .
:lemma-5.2 a vp:Claim ; vp:statedIn :chapter9 ; vp:statement "The Killing form." ; vp:assumes :half ;
    vp:formalizedBy <urn:veriphy:lean:KK.killing_form_value> .
:lemma-8.4 a vp:Claim ; vp:statedIn :chapter9 ; vp:statement "The curvature is positive." ;
    vp:formalizedBy <urn:veriphy:lean:KK.curvature_pos> .
:thm-9.1 a vp:Claim ; vp:statedIn :chapter9 ; vp:statement "The vacuum is stable." ;
    vp:formalizedBy <urn:veriphy:lean:KK.vacuum> ; vp:uses :lemma-5.2, :lemma-8.4 .
:eq-7.3 a vp:Claim ; vp:statedIn :chapter9 ; vp:statement "The metric." ; vp:uses :lemma-5.2 .
:eq-4.1 a vp:Claim ; vp:statedIn :chapter9 ; vp:statement "An estimate." .
"""
PAPER = """<#thm-2> a vp:Claim ; vp:statedIn <#paper> ; vp:statement "The coset curvature." ;
    vp:assumes <urn:veriphy:source:chapter9#one> .
"""
EXPORT = [
    ('KK.killing_form_value', 'Claim', 'certificate'),
    ('KK.curvature_pos', 'Claim', 'oracle-test'),
    ('KK.vacuum', 'Claim', 'certificate'),
    ('KK.half', 'Definition', None),
]
FAKE_CHECKER = """#!/bin/sh
if [ "$1" = rules ]; then cat "{rules}"; exit 0; fi
echo '{report}'
exit {code}
"""
FAKE_REPORTS = {
    'accepted': ({'ok': True, 'verdict': 'entailed', 'theorem': 'OOCert.entails_of_builtin_horn'}, 0),
    'rejected': ({'ok': False, 'first_rejected': 1, 'rule': 'rdfs9'}, 1),
    'unreadable': ({'ok': False, 'error': 'cannot read'}, 2),
}


def _nt(name: str, prop: str, value: str) -> str:
    """Return one N-Triples line of the Lean export."""
    return f'<urn:veriphy:lean:{name}> {prop} {value} .\n'


def export_text() -> str:
    """Return the Lean export of the fixture workspace."""
    lines = []
    for name, cls, level in EXPORT:
        lines.append(_nt(name, '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>', f'<urn:veriphy:vocabulary#{cls}>'))
        lines.append(_nt(name, '<urn:veriphy:vocabulary#leanName>', f'"{name}"'))
        lines.append(_nt(name, '<urn:veriphy:vocabulary#statement>', f'"statement of {name}"'))
        if level:
            lines.append(_nt(name, '<urn:veriphy:vocabulary#hasLevel>', f'<urn:veriphy:vocabulary#{level}>'))
    lines.append(_nt('KK.vacuum', '<urn:veriphy:vocabulary#uses>', '<urn:veriphy:lean:KK.half>'))
    return ''.join(lines)


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """Return a workspace with a chapter, a paper and a Lean export."""
    (tmp_path / 'lakefile.toml').write_text('')
    sources = tmp_path / '.veriphy' / 'graph' / 'sources'
    sources.mkdir(parents=True)
    (sources / 'chapter9.agent.ttl').write_text(PREFIXES + CHAPTER)
    (sources / 'arXiv:0808.3236.human.ttl').write_text(PREFIXES + PAPER)
    lean = tmp_path / '.veriphy' / 'graph' / 'lean'
    lean.mkdir()
    (lean / 'export.nt').write_text(export_text())
    return tmp_path


@pytest.fixture
def checker() -> Path:
    """Return the real `oo-horn`, skipping without it unless `VERIPHY_REQUIRE_CHECKER` is set."""
    path = find_checker().path
    if path is None:
        if os.environ.get('VERIPHY_REQUIRE_CHECKER'):
            pytest.fail('VERIPHY_REQUIRE_CHECKER is set and oo-horn was not found')
        pytest.skip('oo-horn is not built: python -m veriphy.graph checker build')
    return path


@pytest.fixture
def fake_checker(tmp_path: Path) -> Callable[[str], Path]:
    """Return a factory of fake checkers that answer with a fixed status."""

    def make(status: str) -> Path:
        """Return a fake checker that reports `status`."""
        report, code = FAKE_REPORTS[status]
        rules = tmp_path / 'fake-rules.tsv'
        rules.write_text('')
        path = tmp_path / f'oo-horn-{status}'
        path.write_text(FAKE_CHECKER.format(rules=rules, report=json.dumps(report), code=code))
        path.chmod(path.stat().st_mode | stat.S_IEXEC)
        return path

    return make


@pytest.fixture
def committed(workspace: Path) -> Path:
    """Return the workspace as a git repository with everything committed."""
    git = shutil.which('git')
    if git is None:
        pytest.skip('git is not on PATH')
    for args in (
        ['init', '-q'],
        ['add', '-A'],
        ['-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '-m', 'g'],
    ):
        subprocess.run([git, *args], cwd=workspace, check=True, capture_output=True)
    return workspace


@pytest.fixture
def compile_latex(tmp_path: Path) -> Callable[[str], None]:
    """Return a function that compiles a LaTeX fragment in a minimal document, skipping without `pdflatex`."""
    pdflatex = shutil.which('pdflatex')
    if pdflatex is None:
        pytest.skip('pdflatex is not on PATH')

    def compile_fragment(fragment: str) -> None:
        """Compile the fragment, failing the test with the log when LaTeX fails."""
        source = tmp_path / 'appendix.tex'
        source.write_text(f'\\documentclass{{article}}\n\\begin{{document}}\n{fragment}\n\\end{{document}}\n')
        result = subprocess.run(
            [pdflatex, '-interaction=nonstopmode', '-halt-on-error', source.name],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout[-2000:]

    return compile_fragment
