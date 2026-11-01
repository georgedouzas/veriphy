"""Load a project's research graph from `.veriphy/graph/`, with the provenance of every assertion, and edit it."""

from dataclasses import dataclass
from pathlib import Path

from veriphy.core import GraphError, find_workspace_root, project_dir
from veriphy.graph._engine import Triple, parse_rdf, serialize_turtle
from veriphy.graph._vocabulary import (
    LEAN,
    RDF_TYPE,
    SOURCE,
    VOCABULARY,
    source_iri,
    vocabulary_terms,
    vp,
)

GRAPH_DIR = 'graph'
SOURCES_DIR = 'sources'
LEAN_DIR = 'lean'
EDITABLE = ('agent', 'human')
PREFIXES = {'vp': VOCABULARY, 'owl': 'http://www.w3.org/2002/07/owl#'}


def graph_dir(root: Path) -> Path:
    """Return a workspace's `.veriphy/graph/` directory.

    Args:
        root: The Lean workspace root.

    Returns:
        The directory, which may not exist.

    Examples:
        >>> graph_dir(Path('/work/project')).as_posix()
        '/work/project/.veriphy/graph'
    """
    return project_dir(root) / GRAPH_DIR


def _source_file(path: Path) -> tuple[str, str]:
    """Return the source and provenance a file under `sources/` names, or raise."""
    source, dot, provenance = path.name.removesuffix('.ttl').rpartition('.')
    if not dot or provenance not in EDITABLE:
        message = f'{path}: name the file <source>.<provenance>.ttl with provenance agent or human'
        raise GraphError(message)
    return source, provenance


def _parse_file(path: Path, fmt: str, base: str | None) -> list[Triple]:
    """Return a file's triples, naming the file in a parse error."""
    try:
        return parse_rdf(path.read_text(), fmt, base)
    except GraphError as exc:
        message = f'{path}: {exc}'
        raise GraphError(message) from exc


def _check_terms(path: Path, triples: list[Triple], declared: frozenset[str]) -> None:
    """Raise when a file uses a term of the Veriphy namespace that the vocabulary does not declare."""
    for triple in triples:
        for term in triple:
            if term.startswith(f'<{VOCABULARY}') and term not in declared:
                message = f'{path}: {term} is not declared by the Veriphy vocabulary'
                raise GraphError(message)


@dataclass(frozen=True)
class Assertion:
    """An asserted triple with its provenance and the file it comes from.

    Args:
        triple: The triple, in N-Triples spelling.
        provenance: `agent`, `human` or `lean`.
        file: The file that asserts it.
    """

    triple: Triple
    provenance: str
    file: Path


@dataclass(frozen=True)
class ProjectGraph:
    """The research graph of a workspace: every asserted triple, with its provenance.

    Args:
        root: The Lean workspace root.
        assertions: The asserted triples.
        files: Each file read, with its number of triples.
    """

    root: Path
    assertions: tuple[Assertion, ...]
    files: tuple[tuple[Path, int], ...]

    def triples(self) -> frozenset[Triple]:
        """Return the asserted triples.

        Returns:
            Every triple some file asserts.
        """
        return frozenset(a.triple for a in self.assertions)

    def provenance(self, triple: Triple) -> frozenset[str]:
        """Return the provenances with which a triple is asserted.

        Args:
            triple: The triple.

        Returns:
            Its provenances, empty when no file asserts it.
        """
        return frozenset(a.provenance for a in self.assertions if a.triple == triple)

    def nodes_of_type(self, cls: str) -> frozenset[str]:
        """Return the nodes asserted to be of a vocabulary class.

        Args:
            cls: The class's local name, such as `Claim`.

        Returns:
            The nodes, in N-Triples spelling.
        """
        return frozenset(s for s, p, o in self.triples() if p == RDF_TYPE and o == vp(cls))

    def objects(self, subject: str, prop: str) -> tuple[str, ...]:
        """Return the objects of a subject under a vocabulary property, sorted.

        Args:
            subject: The subject, in N-Triples spelling.
            prop: The property's local name.

        Returns:
            The objects.
        """
        return tuple(sorted(o for s, p, o in self.triples() if s == subject and p == vp(prop)))


def load_graph(root: Path | None = None) -> ProjectGraph:
    """Load a workspace's research graph: `sources/<source>.<provenance>.ttl` and the Lean export under `lean/`.

    Args:
        root: The workspace root, found from the working directory when `None`.

    Returns:
        The graph.
    """
    workspace = find_workspace_root(root)
    directory = graph_dir(workspace)
    declared = vocabulary_terms()
    assertions: list[Assertion] = []
    files: list[tuple[Path, int]] = []
    for path in sorted((directory / SOURCES_DIR).glob('*.ttl')):
        source, provenance = _source_file(path)
        triples = _parse_file(path, 'turtle', f'{SOURCE}{source}#')
        _check_terms(path, triples, declared)
        assertions += [Assertion(t, provenance, path) for t in triples]
        files.append((path, len(triples)))
    for path in sorted((directory / LEAN_DIR).glob('*.nt')):
        triples = _parse_file(path, 'ntriples', None)
        _check_terms(path, triples, declared)
        assertions += [Assertion(t, 'lean', path) for t in triples]
        files.append((path, len(triples)))
    return ProjectGraph(workspace, tuple(assertions), tuple(files))


def resolve_term(token: str, source: str, *, predicate: bool = False) -> str:
    """Return the IRI a short term names: `<…>` as written, a vocabulary name as predicate, else a node.

    A node is a label of `source`, `<other source>#<label>` for another source, or `lean:<name>` for a Lean node.

    Args:
        token: The term as typed.
        source: The source a bare label belongs to.
        predicate: Whether the term stands as a predicate.

    Returns:
        The term in N-Triples spelling.

    Examples:
        >>> resolve_term('assumes', 'chapter3', predicate=True)
        '<urn:veriphy:vocabulary#assumes>'
        >>> resolve_term('mostly-minus', 'chapter3')
        '<urn:veriphy:source:chapter3#mostly-minus>'
        >>> resolve_term('arXiv:0808.3236#thm-2', 'chapter3')
        '<urn:veriphy:source:arXiv:0808.3236#thm-2>'
        >>> resolve_term('lean:KK.minkowski', 'chapter3')
        '<urn:veriphy:lean:KK.minkowski>'
    """
    if token.startswith('<') and token.endswith('>'):
        return token
    if predicate:
        return vp(token.removeprefix('vp:'))
    if token.startswith('lean:'):
        return f'<{LEAN}{token.removeprefix("lean:")}>'
    if '#' in token:
        other, label = token.split('#', 1)
        return source_iri(other, label)
    return source_iri(source, token)


def _write(path: Path, triples: set[Triple], source: str) -> None:
    """Write a source file's triples as Turtle with the source's prefix."""
    prefixes = {**PREFIXES, '': f'{SOURCE}{source}#'}
    path.write_text(serialize_turtle(triples, prefixes))


def _file_triples(path: Path, source: str) -> set[Triple]:
    """Return the triples of a source file, empty when it does not exist."""
    return set(_parse_file(path, 'turtle', f'{SOURCE}{source}#')) if path.exists() else set()


def add_triples(root: Path, source: str, provenance: str, triples: set[Triple]) -> Path:
    """Add triples to a source's file of one provenance, creating the file when needed.

    Args:
        root: The Lean workspace root.
        source: The source.
        provenance: `agent` or `human`.
        triples: The triples to add.

    Returns:
        The file written.

    Raises:
        GraphError: When the provenance is not `agent` or `human`.
    """
    if provenance not in EDITABLE:
        message = f"provenance must be 'agent' or 'human', not {provenance!r}"
        raise GraphError(message)
    path = graph_dir(root) / SOURCES_DIR / f'{source}.{provenance}.ttl'
    path.parent.mkdir(parents=True, exist_ok=True)
    _write(path, _file_triples(path, source) | triples, source)
    return path


def confirm(root: Path, source: str, triple: Triple) -> Path:
    """Move one triple from a source's agent file to its human file.

    Args:
        root: The Lean workspace root.
        source: The source.
        triple: The triple to confirm.

    Returns:
        The human file.

    Raises:
        GraphError: When the agent file does not assert the triple.
    """
    agent = graph_dir(root) / SOURCES_DIR / f'{source}.agent.ttl'
    triples = _file_triples(agent, source)
    if triple not in triples:
        message = f'{agent}: does not assert {" ".join(triple)}'
        raise GraphError(message)
    _write(agent, triples - {triple}, source)
    return add_triples(root, source, 'human', {triple})
