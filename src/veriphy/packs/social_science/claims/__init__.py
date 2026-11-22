"""The `social-science` pack's step over the claim graph: `check-concepts`, constructs against a SKOS thesaurus.

A construct a claim uses is a `vp:Concept`, linked by `owl:sameAs` to a concept of a thesaurus, such as ELSST, the
social-science thesaurus of CESSDA, in SKOS. The step checks that every construct names a concept the thesaurus defines,
and reports the label it gives each one. It is evidence about definitions, not about a claim, so it grants no level.
"""

from pathlib import Path

from veriphy.claims import load_graph
from veriphy.claims._vocabulary import RDF_TYPE, SAME_AS, vp
from veriphy.core import content_digest
from veriphy.core._version import __version__
from veriphy.primitives.graph._engine import parse_rdf
from veriphy.steps import Argument, Outcome, Params, Prepared, Step, register

SKOS = 'http://www.w3.org/2004/02/skos/core#'


def _labels(thesaurus: Path) -> dict[str, str]:
    """Return each concept a SKOS thesaurus defines, by IRI, with its preferred label (its IRI when it has none)."""
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
    help="check that every construct the claims use is a concept of a SKOS thesaurus, such as ELSST",
    arguments=(Argument('thesaurus', 'the thesaurus, as SKOS in Turtle'),),
)

register(CHECK_CONCEPTS, pack='social-science')
