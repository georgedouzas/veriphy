"""State the research graph's vocabulary, its node IRIs, and the OWL axioms that give the vocabulary its meaning."""

import re
from collections.abc import Iterable
from importlib.resources import files
from urllib.parse import quote, unquote

from veriphy.graph._engine import Triple, parse_rdf

VOCABULARY = 'urn:veriphy:vocabulary#'
AXIOM = 'urn:veriphy:axiom:'
SOURCE = 'urn:veriphy:source:'
LEAN = 'urn:veriphy:lean:'
OWL = 'http://www.w3.org/2002/07/owl#'
RDF_TYPE = '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>'
SUBCLASS = '<http://www.w3.org/2000/01/rdf-schema#subClassOf>'
SUBPROPERTY = '<http://www.w3.org/2000/01/rdf-schema#subPropertyOf>'
SAME_AS = f'<{OWL}sameAs>'
LEVELS = ('none', 'oracle-test', 'kernel-test', 'lean-proof', 'certificate')
PROVENANCES = ('agent', 'human', 'lean', 'veriphy')
LEAN_SAFE = "._-'"
LITERAL = re.compile(r'^"(?P<body>.*)"(?:@[A-Za-z0-9-]+|\^\^<[^>]*>)?$', re.DOTALL)
ESCAPE = re.compile(r'\\(?:u(?P<u>[0-9A-Fa-f]{4})|U(?P<U>[0-9A-Fa-f]{8})|(?P<c>[tbnrf"\'\\]))')
ESCAPES = {'t': '\t', 'b': '\b', 'n': '\n', 'r': '\r', 'f': '\f', '"': '"', "'": "'", '\\': '\\'}


def vp(name: str) -> str:
    """Return a vocabulary term in N-Triples spelling.

    Args:
        name: The term's local name.

    Returns:
        The term.

    Examples:
        >>> vp('uses')
        '<urn:veriphy:vocabulary#uses>'
    """
    return f'<{VOCABULARY}{name}>'


def source_iri(source: str, label: str) -> str:
    """Return the IRI of a node a source states, in N-Triples spelling.

    Args:
        source: The source identifier: a file stem, an arXiv identifier or a DOI.
        label: The node's label within the source.

    Returns:
        The node's IRI.

    Examples:
        >>> source_iri('arXiv:0808.3236', 'thm-2')
        '<urn:veriphy:source:arXiv:0808.3236#thm-2>'
    """
    return f'<{SOURCE}{source}#{label}>'


def lean_iri(name: str) -> str:
    """Return the IRI of an exported Lean declaration, percent-encoding what is not ASCII alphanumeric or `._-'`.

    Args:
        name: The declaration's full name.

    Returns:
        The declaration's IRI, the same the Lean export writes.

    Examples:
        >>> lean_iri('KK.killing_form_value')
        '<urn:veriphy:lean:KK.killing_form_value>'
        >>> lean_iri('KK.α')
        '<urn:veriphy:lean:KK.%CE%B1>'
    """
    return f'<{LEAN}{quote(name, safe=LEAN_SAFE)}>'


def label_of(iri: str) -> str:
    """Return the short label of a node: the part after `#` for a source node, the Lean name for a Lean node.

    Args:
        iri: The node's IRI in N-Triples spelling.

    Returns:
        The label.

    Examples:
        >>> label_of('<urn:veriphy:source:chapter3#eq-3.12>')
        'eq-3.12'
        >>> label_of('<urn:veriphy:lean:KK.%CE%B1>')
        'KK.α'
    """
    body = iri.strip('<>')
    if body.startswith(LEAN):
        return unquote(body.removeprefix(LEAN))
    return body.rsplit('#', 1)[-1]


def _unescape(match: re.Match[str]) -> str:
    """Return the character an N-Triples escape stands for."""
    code = match.group('u') or match.group('U')
    return chr(int(code, 16)) if code else ESCAPES[match.group('c')]


def literal_text(term: str) -> str:
    r"""Return the text of a literal in N-Triples spelling, or the term itself when it is not a literal.

    Args:
        term: The term.

    Returns:
        The literal's lexical form, unescaped.

    Examples:
        >>> literal_text('"a \\"b\\"\\nc"@en')
        'a "b"\nc'
        >>> literal_text('"3"^^<http://www.w3.org/2001/XMLSchema#integer>')
        '3'
    """
    match = LITERAL.match(term)
    return ESCAPE.sub(_unescape, match.group('body')) if match else term


def source_of(iri: str) -> str:
    """Return the source a node belongs to, `lean` for a Lean node.

    Args:
        iri: The node's IRI in N-Triples spelling.

    Returns:
        The source identifier.

    Examples:
        >>> source_of('<urn:veriphy:source:chapter3#eq-3.12>')
        'chapter3'
        >>> source_of('<urn:veriphy:lean:KK.thm>')
        'lean'
    """
    body = iri.strip('<>')
    if body.startswith(SOURCE):
        return body.removeprefix(SOURCE).rsplit('#', 1)[0]
    return 'lean' if body.startswith(LEAN) else ''


def vocabulary_text() -> str:
    """Return the vocabulary as Turtle.

    Returns:
        The vocabulary document.

    Examples:
        >>> 'vp:none vp:below vp:oracle-test' in vocabulary_text()
        True
    """
    return files('veriphy.graph').joinpath('vocabulary.ttl').read_text()


def vocabulary_triples() -> list[Triple]:
    """Return the vocabulary's triples.

    Returns:
        The triples of the vocabulary document.
    """
    return parse_rdf(vocabulary_text(), 'turtle')


def vocabulary_terms() -> frozenset[str]:
    """Return the terms the vocabulary declares, in N-Triples spelling.

    Returns:
        Every subject of the vocabulary in its namespace.
    """
    return frozenset(s for s, _, _ in vocabulary_triples() if s.startswith(f'<{VOCABULARY}'))


def _axiom(name: str) -> str:
    """Return a generated class's IRI."""
    return f'<{AXIOM}{quote(name, safe=LEAN_SAFE + ":#")}>'


def _restriction(node: str, prop: str, kind: str, value: str) -> list[Triple]:
    """Return the two triples of an OWL restriction."""
    return [(node, f'<{OWL}onProperty>', prop), (node, f'<{OWL}{kind}>', value)]


def _propagation(target: str, name: str, links: Iterable[tuple[str, str]]) -> list[Triple]:
    """Return, for each link property, a class of the nodes linked to a member of `target`, inside `target`."""
    triples: list[Triple] = []
    for tag, prop in links:
        node = _axiom(f'{tag}/{name}')
        triples += [*_restriction(node, prop, 'someValuesFrom', target), (node, SUBCLASS, target)]
    return triples


def generate_axioms(conventions: Iterable[str]) -> list[Triple]:
    """Return the OWL axioms that make `assumes` and level caps follow the graph's links under the built-in rules.

    For each convention `k`, the class of nodes that assume `k` is a `hasValue` restriction, and the nodes that use,
    are `owl:sameAs`, or are formalized by a member are inside it. For each level, the same holds for `cappedAt`
    through `uses` and `formalizedBy`, and each level's class is inside the class of the next level up.

    Args:
        conventions: The conventions of the graph, in N-Triples spelling.

    Returns:
        The axioms, whose generated classes are IRIs under `urn:veriphy:axiom:`.

    Examples:
        >>> axioms = generate_axioms(['<urn:veriphy:source:ch#k>'])
        >>> ('<urn:veriphy:vocabulary#realizes>', '<http://www.w3.org/2002/07/owl#inverseOf>',
        ...  '<urn:veriphy:vocabulary#realizedBy>') in axioms
        True
        >>> len(generate_axioms(['<urn:veriphy:source:ch#k>', '<urn:veriphy:source:ch#j>'])) - len(axioms)
        11
    """
    triples: list[Triple] = [
        (vp('realizes'), f'<{OWL}inverseOf>', vp('realizedBy')),
        (vp('realizes'), SUBPROPERTY, vp('assumes')),
        (vp('hasLevel'), SUBPROPERTY, vp('cappedAt')),
    ]
    for convention in sorted(set(conventions)):
        name = f'assumes/{convention.strip("<>")}'
        target = _axiom(name)
        triples += _restriction(target, vp('assumes'), 'hasValue', convention)
        triples += _propagation(target, name, [('uses', vp('uses')), ('same', SAME_AS), ('formal', vp('formalizedBy'))])
    for index, level in enumerate(LEVELS):
        name = f'capped/{level}'
        target = _axiom(name)
        triples += _restriction(target, vp('cappedAt'), 'hasValue', vp(level))
        triples += _propagation(target, name, [('uses', vp('uses')), ('formal', vp('formalizedBy'))])
        if index + 1 < len(LEVELS):
            triples.append((target, SUBCLASS, _axiom(f'capped/{LEVELS[index + 1]}')))
    return triples
