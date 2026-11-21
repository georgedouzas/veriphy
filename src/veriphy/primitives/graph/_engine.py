"""Reach the research graph's optional dependencies: the RDF parser, the Horn reasoner and the SHACL validator."""

import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from veriphy.core import GraphError, GraphExtraMissingError

Triple = tuple[str, str, str]

FORMATS = {'turtle': 'TURTLE', 'ntriples': 'N_TRIPLES'}


def _oxigraph() -> ModuleType:
    """Return `pyoxigraph`, or raise the error that says how to install it."""
    try:
        import pyoxigraph  # noqa: PLC0415 - optional dependency, from the graph extra
    except ModuleNotFoundError as exc:
        module = 'pyoxigraph'
        raise GraphExtraMissingError(module) from exc
    return pyoxigraph


def _horn(source: Path) -> ModuleType:
    """Return the Horn reasoner of `open-ontologies-lite`, imported from a release's source directory."""
    path = str(source)
    if sys.path[:1] != [path]:
        while path in sys.path:
            sys.path.remove(path)
        sys.path.insert(0, path)
    loaded = sys.modules.get('open_ontologies_lite')
    if loaded is not None and not str(getattr(loaded, '__file__', '')).startswith(path):
        for name in [n for n in sys.modules if n == 'open_ontologies_lite' or n.startswith('open_ontologies_lite.')]:
            del sys.modules[name]
    try:
        from open_ontologies_lite import horn  # noqa: PLC0415 - optional dependency, from the cached release
    except ModuleNotFoundError as exc:
        module = 'open_ontologies_lite'
        raise GraphExtraMissingError(module) from exc
    return horn


def _shacl() -> tuple[ModuleType, ModuleType]:
    """Return `rdflib` and `pyshacl`, or raise the error that says how to install them."""
    try:
        import pyshacl  # noqa: PLC0415 - optional dependency, from the graph extra
        import rdflib  # noqa: PLC0415 - optional dependency, installed with pyshacl
    except ModuleNotFoundError as exc:
        module = exc.name or 'pyshacl'
        raise GraphExtraMissingError(module) from exc
    return rdflib, pyshacl


def _spell(term: object) -> str:
    """Return a parsed term in N-Triples spelling."""
    return str(term)


def parse_rdf(text: str, fmt: str, base: str | None = None) -> list[Triple]:
    """Return the triples of a Turtle or N-Triples document, in N-Triples spelling.

    Args:
        text: The document.
        fmt: `turtle` or `ntriples`.
        base: The base IRI that relative IRIs resolve against.

    Returns:
        The triples, in document order.

    Raises:
        GraphError: When the document does not parse or holds a blank node, with the parser's message.
    """
    ox = _oxigraph()
    try:
        quads = list(ox.parse(text.encode(), format=getattr(ox.RdfFormat, FORMATS[fmt]), base_iri=base))
    except SyntaxError as exc:
        raise GraphError(str(exc)) from exc
    triples = []
    for quad in quads:
        if isinstance(quad.subject, ox.BlankNode) or isinstance(quad.object, ox.BlankNode):
            message = f'blank nodes are not allowed, give the node an IRI: {quad}'
            raise GraphError(message)
        triples.append((_spell(quad.subject), _spell(quad.predicate), _spell(quad.object)))
    return triples


def serialize_turtle(triples: Iterable[Triple], prefixes: dict[str, str]) -> str:
    """Return triples as a Turtle document with the given prefixes.

    Args:
        triples: The triples, in N-Triples spelling.
        prefixes: The prefix names and their IRIs.

    Returns:
        The document.
    """
    ox = _oxigraph()
    lines = ''.join(f'{s} {p} {o} .\n' for s, p, o in sorted(triples))
    quads = list(ox.parse(lines.encode(), format=ox.RdfFormat.N_TRIPLES))
    data = ox.serialize(quads, format=ox.RdfFormat.TURTLE, prefixes=prefixes)
    return data.decode() if data else ''


@dataclass(frozen=True)
class ReasonerOutput:
    """The result of a Horn run, before the checker sees it.

    Args:
        fixpoint: Whether the run reached its fixpoint.
        iterations: The number of rounds it ran.
        derived: The number of derived triples.
    """

    fixpoint: bool
    iterations: int
    derived: int


def run_reasoner(triples: Sequence[Triple], directory: Path, source: Path) -> ReasonerOutput:
    """Derive the closure of triples under the checker's built-in rules, and write the certificate into a directory.

    Args:
        triples: The asserted triples, whose terms are IRIs.
        directory: The certificate directory.
        source: The release source directory the reasoner is imported from.

    Returns:
        What the run reached.
    """
    ox, horn = _oxigraph(), _horn(source)
    store = ox.Store()
    lines = ''.join(f'{s} {p} {o} .\n' for s, p, o in triples)
    store.load(lines.encode(), format=ox.RdfFormat.N_TRIPLES)
    result = horn.run_horn(store, certificate_dir=directory)
    return ReasonerOutput(result.fixpoint_reached, result.iterations, result.derived_triples)


def validate_shacl(data: Iterable[Triple], shapes: str) -> list[dict[str, str]]:
    """Return the SHACL violations of data against shapes, one dictionary per result.

    Args:
        data: The data triples, in N-Triples spelling.
        shapes: The shapes, as Turtle.

    Returns:
        For each violation, its focus node, its path, its source shape and its message, as N-Triples spellings.
    """
    rdflib, pyshacl = _shacl()
    graph = rdflib.Graph().parse(data=''.join(f'{s} {p} {o} .\n' for s, p, o in data), format='nt')
    shapes_graph = rdflib.Graph().parse(data=shapes, format='turtle')
    _, report, _ = pyshacl.validate(graph, shacl_graph=shapes_graph)
    sh = rdflib.Namespace('http://www.w3.org/ns/shacl#')
    results = []
    for result in report.subjects(rdflib.RDF.type, sh.ValidationResult):
        fields = {'focus': sh.focusNode, 'path': sh.resultPath, 'shape': sh.sourceShape, 'message': sh.resultMessage}
        row = {key: report.value(result, value) for key, value in fields.items()}
        results.append({key: (value.n3() if value is not None else '') for key, value in row.items()})
    return results
