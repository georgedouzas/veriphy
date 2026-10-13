"""Test Christoffel symbols, primitives and contractions in coordinates."""

from collections.abc import Callable

import pytest
from sage.all import SR, cos, diagonal_matrix, matrix, sin, var

from veriphy.core import CertificateError
from veriphy.toolkit import (
    Lean,
    christoffel_proof,
    christoffel_symbols,
    coordinates,
    exact_form_proof,
    field_invariant,
    killing_proof,
    metric_term,
    primitive,
)


def test_sphere_christoffel_symbols() -> None:
    """The 2-sphere has Γ^θ_φφ = -sin θ cos θ and Γ^φ_θφ = cot θ; Minkowski space has none."""
    x0, _ = coordinates(2)
    symbols = christoffel_symbols(matrix(SR, [[1, 0], [0, sin(x0) ** 2]]))
    assert symbols[(0, 1, 1)] == -cos(x0) * sin(x0)
    assert (symbols[(1, 0, 1)] - cos(x0) / sin(x0)).simplify_full() == 0
    assert christoffel_symbols(diagonal_matrix(SR, [1, -1, -1, -1])) == {}


def test_primitive_and_closedness() -> None:
    """A closed form has a primitive; a form that is not closed is refused."""
    x0, x1 = coordinates(2)
    f = primitive([x1, x0])
    assert f == x0 * x1
    with pytest.raises(CertificateError, match='not closed'):
        primitive([x1, -x0])


def test_degenerate_metric_and_invariant() -> None:
    """A degenerate metric is refused; the field invariant of a pure electric field is -2E²."""
    x0, _ = coordinates(2)
    with pytest.raises(CertificateError, match='degenerate'):
        christoffel_proof(matrix(SR, [[x0, x0], [x0, x0]]), metric='g')
    e = var('E')
    f = matrix(SR, [[0, -e, 0, 0], [e, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
    assert field_invariant(f, diagonal_matrix(SR, [1, -1, -1, -1])) == -2 * e**2


def test_geometry_proofs_parse_in_lean(lean_parses: Callable[[list[Lean]], str]) -> None:
    """The proofs parse as Lean tactics, and the metric renders as a component family."""
    x0, _ = coordinates(2)
    g = matrix(SR, [[1, 0], [0, sin(x0) ** 2]])
    assert metric_term(g).startswith('(![![fun x => (1 : ℝ), fun x => (0 : ℝ)]')
    proofs = [christoffel_proof(g, metric='g', unfold=['g']), killing_proof(unfold=['g']), exact_form_proof(x0, 2)]
    assert lean_parses(proofs) == ''
