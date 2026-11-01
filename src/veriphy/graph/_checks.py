"""Check a research graph: SHACL shapes as a measurement, exclusive conventions, and clashes from checked runs."""

from dataclasses import dataclass
from importlib.resources import files
from itertools import combinations
from pathlib import Path

from veriphy.graph._engine import Triple, validate_shacl
from veriphy.graph._reasoning import Run
from veriphy.graph._store import ProjectGraph
from veriphy.graph._vocabulary import AXIOM, label_of, vocabulary_triples, vp


def shapes_text() -> str:
    """Return the shapes a research graph conforms to, as Turtle.

    Returns:
        The shapes document.

    Examples:
        >>> 'sh:targetClass vp:Claim' in shapes_text()
        True
    """
    return files('veriphy.graph').joinpath('shapes.ttl').read_text()


@dataclass(frozen=True)
class ShapeViolation:
    """A node that breaks a shape.

    Args:
        focus: The node, in N-Triples spelling.
        path: The property the shape constrains, if any.
        message: The shape's message.
        files: The files that assert something about the node.
    """

    focus: str
    path: str
    message: str
    files: tuple[Path, ...]


@dataclass(frozen=True)
class ShapeReport:
    """The SHACL validator's measurement of a graph.

    Args:
        violations: The violations, empty when the graph conforms.
    """

    violations: tuple[ShapeViolation, ...]

    @property
    def conforms(self) -> bool:
        """Whether the validator found no violation."""
        return not self.violations


def validate_shapes(graph: ProjectGraph) -> ShapeReport:
    """Validate a graph, with the vocabulary, against the shapes.

    Args:
        graph: The research graph.

    Returns:
        The report.
    """
    data = graph.triples() | set(vocabulary_triples())
    violations = []
    for row in validate_shacl(data, shapes_text()):
        focus = row['focus']
        sources = tuple(sorted({a.file for a in graph.assertions if a.triple[0] == focus}))
        violations.append(ShapeViolation(focus, row['path'], row['message'].strip('"'), sources))
    return ShapeReport(tuple(sorted(violations, key=lambda v: (v.focus, v.message))))


def shape_report(report: ShapeReport) -> str:
    """Return a shapes report, labelled as the validator's measurement.

    Args:
        report: The report.

    Returns:
        The report as text.
    """
    if report.conforms:
        return 'The graph conforms to every shape, according to the SHACL validator (a measurement, not a check).\n'
    lines = [f'The SHACL validator reports {len(report.violations)} violations (a measurement, not a check):']
    for v in report.violations:
        where = ', '.join(str(f) for f in v.files)
        lines.append(f'- {label_of(v.focus)}: {v.message} ({where})')
    return '\n'.join(lines) + '\n'


def _aspects(graph: ProjectGraph) -> dict[str, list[str]]:
    """Return the conventions of each aspect that `conventionFor` names."""
    aspects: dict[str, list[str]] = {}
    for s, p, o in sorted(graph.triples()):
        if p == vp('conventionFor'):
            aspects.setdefault(o, []).append(s)
    return aspects


def _excluded(graph: ProjectGraph, first: str, second: str) -> bool:
    """Return whether the graph asserts that two conventions exclude each other, in either order."""
    triples = graph.triples()
    return (first, vp('excludes'), second) in triples or (second, vp('excludes'), first) in triples


def propose_excludes(graph: ProjectGraph) -> tuple[Triple, ...]:
    """Return the `excludes` triples that conventions of the same aspect imply and the graph does not assert yet.

    Args:
        graph: The research graph.

    Returns:
        The proposed triples, sorted.
    """
    proposed = [
        (first, vp('excludes'), second)
        for conventions in _aspects(graph).values()
        for first, second in combinations(sorted(conventions), 2)
        if not _excluded(graph, first, second)
    ]
    return tuple(proposed)


@dataclass(frozen=True)
class Clash:
    """A node that assumes two conventions which exclude each other.

    Args:
        node: The node, in N-Triples spelling.
        first: The first convention.
        second: The second convention.
        checked: Whether both `assumes` conclusions come from a run the checker accepted.
    """

    node: str
    first: str
    second: str
    checked: bool


def clashes(graph: ProjectGraph, run: Run) -> tuple[Clash, ...]:
    """Return every node with two `assumes` conclusions of a run whose conventions exclude each other.

    Args:
        graph: The research graph, which asserts the `excludes` triples.
        run: A run of the graph.

    Returns:
        The clashes, sorted.
    """
    assumed: dict[str, set[str]] = {}
    for s, p, o in run.asserted | run.derived:
        if p == vp('assumes') and not s.startswith(f'<{AXIOM}'):
            assumed.setdefault(s, set()).add(o)
    found = [
        Clash(node, first, second, run.checked)
        for node, conventions in sorted(assumed.items())
        for first, second in combinations(sorted(conventions), 2)
        if _excluded(graph, first, second)
    ]
    return tuple(found)


def clash_report(found: tuple[Clash, ...], run: Run) -> str:
    """Return a clash report, saying that the absence of a clash is not a checked conclusion.

    Args:
        found: The clashes, from `clashes`.
        run: The run they come from.

    Returns:
        The report as text.
    """
    if not found:
        return (
            f'No clash (run {run.directory.name}: {run.label}). The absence of a clash is the reasoner\'s result, not '
            'a checked conclusion.\n'
        )
    lines = [f'{len(found)} clashes (run {run.directory.name}: {run.label}):']
    lines += [f'- {label_of(c.node)} assumes {label_of(c.first)} and {label_of(c.second)}' for c in found]
    return '\n'.join(lines) + '\n'
