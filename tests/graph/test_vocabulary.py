"""Test the research graph's vocabulary, node IRIs and generated axioms."""

from itertools import pairwise

from veriphy.graph import (
    generate_axioms,
    label_of,
    lean_iri,
    source_iri,
    source_of,
    vocabulary_terms,
    vocabulary_triples,
    vp,
)

SPEC_TERMS = [
    'Claim',
    'Convention',
    'Concept',
    'Source',
    'uses',
    'assumes',
    'defines',
    'statedIn',
    'statement',
    'leanName',
    'formalizedBy',
    'realizedBy',
    'hasLevel',
    'conventionFor',
    'excludes',
    'none',
    'oracle-test',
    'kernel-test',
    'certificate',
]


def test_vocabulary_terms_declares_every_spec_term() -> None:
    """Declare every class, property and level the spec lists."""
    terms = vocabulary_terms()
    assert all(vp(name) in terms for name in SPEC_TERMS)


def test_vocabulary_terms_orders_the_levels() -> None:
    """State none below oracle-test below kernel-test below certificate."""
    order = {(s, o) for s, p, o in vocabulary_triples() if p == vp('below')}
    assert order == {
        (vp('none'), vp('oracle-test')),
        (vp('oracle-test'), vp('kernel-test')),
        (vp('kernel-test'), vp('certificate')),
    }


def test_source_iri_keeps_same_labels_apart() -> None:
    """Give the same label in two sources two IRIs."""
    assert source_iri('chapter3', 'lemma-1') != source_iri('chapter5', 'lemma-1')
    assert source_of(source_iri('arXiv:0808.3236', 'thm-2')) == 'arXiv:0808.3236'


def test_lean_iri_is_stable_and_reversible() -> None:
    """Give a Lean name the same IRI every time, and read the name back."""
    assert lean_iri('KK.Coset.killing_form_value') == lean_iri('KK.Coset.killing_form_value')
    assert label_of(lean_iri('KK.«a b».α')) == 'KK.«a b».α'


def test_generate_axioms_uses_only_axiom_iris() -> None:
    """Give generated classes IRIs under urn:veriphy:axiom:, never blank nodes."""
    axioms = generate_axioms([source_iri('ch', 'k')])
    subjects = {s for s, _, _ in axioms if not s.startswith('<urn:veriphy:vocabulary#')}
    assert subjects
    assert all(s.startswith('<urn:veriphy:axiom:') for s in subjects)


def test_generate_axioms_grows_linearly() -> None:
    """Add the same number of axioms for every convention."""
    counts = [len(generate_axioms([source_iri('ch', f'k{i}') for i in range(n)])) for n in range(4)]
    assert len({b - a for a, b in pairwise(counts)}) == 1
