"""The framework's step `check-concepts`: the constructs of the claim graph against a vocabulary of the field.

A construct a claim uses is a `vp:Concept`, linked by `owl:sameAs` to a concept of a vocabulary: a SKOS thesaurus in
Turtle, such as ELSST for the social sciences or the JEL classification for economics, read with rdflib; or an OBO or
OWL ontology, such as the Gene Ontology, read with pronto (`veriphy[life-sciences]`). The step checks that every
construct names a concept the vocabulary defines, and reports the label it gives each one. It is evidence about
definitions, not about a claim, so it grants no level.
"""

from pathlib import Path

from veriphy.claims import load_graph
from veriphy.claims._vocabulary import RDF_TYPE, SAME_AS, vp
from veriphy.core import StepError, content_digest
from veriphy.core._version import __version__
from veriphy.primitives.graph._engine import parse_rdf
from veriphy.steps import Argument, Outcome, Params, Prepared, Step

SKOS = 'http://www.w3.org/2004/02/skos/core#'


OBO = 'http://purl.obolibrary.org/obo/'


def _ontology_labels(path: Path) -> dict[str, str]:
    """Return each term an OBO or OWL ontology defines, by its IRI, with its name, read with pronto."""
    try:
        import pronto  # noqa: PLC0415 - an optional library, which only an ontology needs
    except ModuleNotFoundError as exc:
        message = f"reading {path.name} needs pronto: install it with `pip install 'veriphy[life-sciences]'`"
        raise StepError(message) from exc
    ontology = pronto.Ontology(str(path))
    return {f"<{OBO}{term.id.replace(':', '_')}>": term.name or term.id for term in ontology.terms()}


def _labels(thesaurus: Path) -> dict[str, str]:
    """Return each concept a vocabulary defines, by IRI, with its label: a SKOS thesaurus, or an OBO or OWL ontology."""
    if thesaurus.suffix in {'.obo', '.owl'}:
        return _ontology_labels(thesaurus)
    triples = parse_rdf(thesaurus.read_text(), 'turtle')
    concepts = {s for s, p, o in triples if p == RDF_TYPE and o == f'<{SKOS}Concept>'}
    labels = {s: o.split('"')[1] for s, p, o in triples if p == f'<{SKOS}prefLabel>' and s in concepts}
    return {concept: labels.get(concept, concept.strip('<>')) for concept in concepts}


def _prepare(root: Path, params: Params) -> Prepared:
    """Read the graph and the thesaurus, whose content the digest covers."""
    graph = load_graph(root)
    path = Path(str(params['thesaurus']))
    thesaurus = path if path.is_absolute() else root / path
    triples = ''.join(f'{s} {p} {o} .\n' for s, p, o in sorted(graph.triples()))
    contents = {'graph': triples, 'thesaurus': content_digest(thesaurus.read_bytes())}
    return Prepared(contents, {'thesaurus': str(thesaurus)}, context=(graph, thesaurus))


def _check(_root: Path, _params: Params, prepared: Prepared) -> Outcome:
    """Check that every construct of the graph names a concept the thesaurus defines."""
    context = prepared.context
    if not isinstance(context, tuple):
        message = 'check-concepts must prepare the graph and the thesaurus'
        raise TypeError(message)
    graph, thesaurus = context
    labels = _labels(Path(thesaurus))
    constructs = sorted(graph.nodes_of_type('Concept'))
    matched: dict[str, str] = {}
    violations: list[str] = []
    for construct in constructs:
        name = construct.strip('<>').rsplit('#', 1)[-1]
        linked = [o for s, p, o in graph.triples() if s == construct and p == SAME_AS]
        known = [o for o in linked if o in labels]
        if known:
            matched[name] = labels[known[0]]
        elif linked:
            violations.append(f'{name} names {", ".join(linked)}, which the thesaurus does not define')
        else:
            violations.append(f'{name} names no thesaurus concept: link it with owl:sameAs')
    used = {o for s, p, o in graph.triples() if p == vp('uses') and o in constructs}
    outputs: dict[str, object] = {
        'concepts': matched,
        'violations': violations,
        'unused': sorted(c.strip('<>').rsplit('#', 1)[-1] for c in set(constructs) - used),
    }
    return Outcome('violations' if violations else 'conforms', outputs, {'veriphy': __version__})


CHECK_CONCEPTS = Step(
    'check-concepts',
    'evidence',
    _prepare,
    _check,
    help='check that every construct the claims use is a concept of a vocabulary: a SKOS thesaurus, or an ontology',
    arguments=(Argument('thesaurus', 'the vocabulary: SKOS in Turtle (.ttl), or an OBO or OWL ontology'),),
)
