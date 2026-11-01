"""Reason over a research graph with the Horn reasoner, write the certificate, and have `oo-horn` check it."""

import hashlib
import json
import shutil
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from veriphy.core import CheckerError, GraphError
from veriphy.graph._checker import (
    BUILD_COMMAND,
    Setup,
    check_certificate,
    ensure_checker,
    ensure_reasoner,
    find_checker,
    setup_enabled,
)
from veriphy.graph._engine import Triple, run_reasoner
from veriphy.graph._store import ProjectGraph, graph_dir
from veriphy.graph._vocabulary import generate_axioms, vp

RUNS_DIR = 'runs'
DIGEST_FILE = 'asserted.sha256'
RUN_FILE = 'run.json'
CHECK_FILE = 'check.json'
DIGEST_LENGTH = 12


def _is_iri_triple(triple: Triple) -> bool:
    """Return whether every term of a triple is an IRI, which is what the reasoner and the checker read."""
    return all(term.startswith('<') for term in triple)


def _digest(triples: Iterable[Triple]) -> str:
    """Return the SHA-256 of a set of triples, one sorted N-Triples line each."""
    lines = ''.join(f'{s} {p} {o} .\n' for s, p, o in sorted(set(triples)))
    return hashlib.sha256(lines.encode()).hexdigest()


def _conventions(graph: ProjectGraph) -> set[str]:
    """Return the graph's conventions: the declared ones and every object of `assumes`."""
    assumed = {o for _, p, o in graph.triples() if p == vp('assumes')}
    return set(graph.nodes_of_type('Convention')) | assumed


def _unlevelled_claims(graph: ProjectGraph) -> list[Triple]:
    """Return `hasLevel none` for each claim with neither a level nor a formalization."""
    linked = {s for s, p, _ in graph.triples() if p in {vp('hasLevel'), vp('formalizedBy')}}
    return [(c, vp('hasLevel'), vp('none')) for c in sorted(graph.nodes_of_type('Claim') - linked)]


def reasoning_input(graph: ProjectGraph) -> list[Triple]:
    """Return what a run of a graph asserts: its IRI triples, `hasLevel none` for unlevelled claims, and the axioms.

    Args:
        graph: The research graph.

    Returns:
        The asserted triples of the run, sorted.
    """
    triples = {t for t in graph.triples() if _is_iri_triple(t)}
    triples |= set(_unlevelled_claims(graph)) | set(generate_axioms(_conventions(graph)))
    return sorted(triples)


@dataclass(frozen=True)
class Step:
    """One line of a certificate: a rule, its conclusion and its premises.

    Args:
        rule: The rule's name.
        conclusion: The derived triple.
        premises: The triples the rule's body matched, asserted or concluded by an earlier line.
    """

    rule: str
    conclusion: Triple
    premises: tuple[Triple, ...]


@dataclass(frozen=True)
class Run:
    """A reasoning run and what the checker said about it.

    Args:
        directory: The certificate directory.
        status: `accepted`, `rejected`, `unreadable`, `unchecked_no_checker` or `unchecked_error`.
        verdict: The checker's verdict word when it accepted the run, else `None`.
        theorem: The theorem the checker named when it accepted the run, else `None`.
        complete: Whether the run reached its fixpoint.
        digest: The SHA-256 of the asserted triples.
        asserted: The asserted triples.
        steps: The certificate's lines.
        report: The checker's report, or why there is none.
    """

    directory: Path
    status: str
    verdict: str | None
    theorem: str | None
    complete: bool
    digest: str
    asserted: frozenset[Triple]
    steps: tuple[Step, ...]
    report: dict[str, object]

    @property
    def checked(self) -> bool:
        """Whether the checker accepted a complete run."""
        return self.status == 'accepted' and self.complete

    @property
    def derived(self) -> frozenset[Triple]:
        """The triples the run concluded."""
        return frozenset(step.conclusion for step in self.steps)

    @property
    def label(self) -> str:
        """The word a report shows for the run: the checker's verdict, or `unchecked`, `rejected` or `incomplete`."""
        if not self.complete:
            return 'incomplete'
        if self.status == 'accepted':
            return str(self.verdict)
        return 'rejected' if self.status in {'rejected', 'unreadable'} else 'unchecked'

    def holds(self, triple: Triple) -> bool:
        """Return whether a triple is asserted or concluded by the run.

        Args:
            triple: The triple.

        Returns:
            Whether the run has it.
        """
        return triple in self.asserted or triple in self.derived


def _fields(line: str) -> list[str]:
    """Return the tab-separated fields of a certificate line."""
    return line.rstrip('\n').split('\t')


def _read_steps(directory: Path) -> tuple[Step, ...]:
    """Return the lines of a certificate, using the rule table for each rule's name and body size."""
    rules = [_fields(line) for line in (directory / 'rules.tsv').read_text().splitlines() if line.strip()]
    steps = []
    for line in (directory / 'horn.tsv').read_text().splitlines():
        if not line.strip():
            continue
        fields = _fields(line)
        name, body = rules[int(fields[0])][0], int(rules[int(fields[0])][1])
        start = 2 + 2 * int(fields[1])
        terms = fields[start:]
        triples = [(terms[i], terms[i + 1], terms[i + 2]) for i in range(0, 3 * (body + 1), 3)]
        steps.append(Step(name, triples[0], tuple(triples[1:])))
    return tuple(steps)


def _read_asserted(directory: Path) -> frozenset[Triple]:
    """Return the asserted triples of a certificate."""
    lines = (directory / 'asserted.tsv').read_text().splitlines()
    return frozenset((f[0], f[1], f[2]) for f in (_fields(line) for line in lines if line.strip()))


def load_run(directory: Path) -> Run:
    """Read a stored run: its certificate, its digest and the checker's report.

    Args:
        directory: The run directory.

    Returns:
        The run.

    Raises:
        GraphError: When the directory is not a run Veriphy wrote.
    """
    try:
        meta = json.loads((directory / RUN_FILE).read_text())
        report = json.loads((directory / CHECK_FILE).read_text())
        digest = (directory / DIGEST_FILE).read_text().strip()
        steps, asserted = _read_steps(directory), _read_asserted(directory)
    except (OSError, ValueError, IndexError) as exc:
        message = f'{directory}: not a reasoning run ({exc})'
        raise GraphError(message) from exc
    status = str(report.get('status'))
    accepted = status == 'accepted'
    return Run(
        directory,
        status,
        str(report.get('verdict')) if accepted else None,
        str(report.get('theorem')) if accepted else None,
        bool(meta.get('fixpoint')),
        digest,
        asserted,
        steps,
        report,
    )


def _unchecked(status: str, searched: tuple[Path, ...], error: str) -> dict[str, object]:
    """Return the report of a run no checker saw, with where Veriphy looked and how to set the checker up."""
    return {'status': status, 'searched': [str(p) for p in searched], 'build': BUILD_COMMAND, 'error': error}


def _check(directory: Path, checker: Path | None, setup: Setup) -> dict[str, object]:
    """Return the checker's report on a certificate, setting the checker up on first use, or say why there is none."""
    if checker is not None:
        return check_certificate(directory, checker)
    lookup = find_checker(release=setup.release)
    if lookup.path is not None:
        return check_certificate(directory, lookup.path)
    if lookup.explicit or not setup_enabled():
        reason = 'the explicit checker is missing' if lookup.explicit else 'VERIPHY_GRAPH_SETUP is off'
        return _unchecked('unchecked_no_checker', lookup.searched, reason)
    try:
        path = ensure_checker(release=setup.release, notify=setup.notify)
    except CheckerError as exc:
        return _unchecked('unchecked_error', lookup.searched, f'setting up the checker failed: {exc}')
    return check_certificate(directory, path)


def check_run(directory: Path, checker: Path | None = None, setup: Setup | None = None) -> Run:
    """Check a run directory with `oo-horn`, record the report, and return the run.

    Args:
        directory: The run directory.
        checker: The `oo-horn` executable, found or set up on first use when `None`.
        setup: Where first-use setup fetches from and reports to, the pinned release and standard error by default.

    Returns:
        The run, with the checker's report.
    """
    report = _check(directory, checker, setup or Setup())
    (directory / CHECK_FILE).write_text(json.dumps(report, indent=1, sort_keys=True) + '\n')
    return load_run(directory)


def reason_triples(
    triples: Iterable[Triple],
    runs: Path,
    checker: Path | None = None,
    setup: Setup | None = None,
) -> Run:
    """Reason over asserted triples, write the run under `runs/<digest>/`, and have it checked.

    Args:
        triples: The asserted triples, whose terms are IRIs.
        runs: The directory that holds runs.
        checker: The `oo-horn` executable, found or set up on first use when `None`.
        setup: Where first-use setup fetches from and reports to, the pinned release and standard error by default.

    Returns:
        The checked run.
    """
    setup = setup or Setup()
    asserted = sorted(set(triples))
    digest = _digest(asserted)
    directory = runs / digest[:DIGEST_LENGTH]
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True)
    output = run_reasoner(asserted, directory, ensure_reasoner(release=setup.release, notify=setup.notify))
    (directory / DIGEST_FILE).write_text(digest + '\n')
    meta = {'fixpoint': output.fixpoint, 'iterations': output.iterations, 'derived': output.derived}
    (directory / RUN_FILE).write_text(json.dumps(meta, indent=1, sort_keys=True) + '\n')
    return check_run(directory, checker, setup)


def reason(graph: ProjectGraph, checker: Path | None = None, setup: Setup | None = None) -> Run:
    """Reason over a project's graph under the built-in rules, and have the certificate checked.

    The reasoner and the checker are set up on first use unless `VERIPHY_GRAPH_SETUP` is `off`.

    Args:
        graph: The research graph.
        checker: The `oo-horn` executable, found or set up on first use when `None`.
        setup: Where first-use setup fetches from and reports to, the pinned release and standard error by default.

    Returns:
        The checked run, stored under `.veriphy/graph/runs/`.
    """
    return reason_triples(reasoning_input(graph), graph_dir(graph.root) / RUNS_DIR, checker, setup)


def recheck(directory: Path, graph: ProjectGraph | None = None, checker: Path | None = None) -> tuple[Run, bool | None]:
    """Check a stored run again, and say whether the current graph still asserts the same triples.

    Args:
        directory: The run directory.
        graph: The current graph, or `None` to skip the comparison.
        checker: The `oo-horn` executable, found with `find_checker` when `None`.

    Returns:
        The rechecked run, and whether its digest matches the graph (`None` without a graph).
    """
    run = check_run(directory, checker)
    matches = None if graph is None else _digest(reasoning_input(graph)) == run.digest
    return run, matches
