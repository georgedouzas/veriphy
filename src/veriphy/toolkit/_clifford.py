"""Gamma matrices and Clifford-algebra identities, checked by the kernel over the Gaussian integers ℤ[i].

Sage builds gamma matrices in a representation and signature, checks the Clifford relation, and computes traces,
contractions and Fierz coefficients. Each claim reaches Lean as one statement quantified over all indices, about
explicit matrices over mathlib's `GaussianInt`, proved by `decide +kernel`: the kernel evaluates every index
combination. The statements take the matrices as arguments of a `fun`, so they need no definitions.
"""

import itertools
from collections.abc import Sequence

from sage.all import QQ, QuadraticField, identity_matrix, matrix, vector
from sage.matrix.matrix0 import Matrix

from veriphy.core import CertificateError
from veriphy.toolkit._lean import Lean, tactic

FIELD = QuadraticField(-1, 'i')
I = FIELD.gen()
PAULI = [matrix(FIELD, [[0, 1], [1, 0]]), matrix(FIELD, [[0, -I], [I, 0]]), matrix(FIELD, [[1, 0], [0, -1]])]
SPACETIME = 4
CLASSES = ('S', 'V', 'T', 'A', 'P')
KERNEL = 'set_option maxRecDepth 100000 in\ndecide +kernel'


def _block(a: Matrix, b: Matrix, c: Matrix, d: Matrix) -> Matrix:
    """Return the 4×4 block matrix `[[a, b], [c, d]]`."""
    return matrix(FIELD, 4, 4, lambda i, j: (a, b, c, d)[2 * (i // 2) + j // 2][i % 2, j % 2])


def gamma_matrices(representation: str = 'dirac', signature: str = 'mostly_minus') -> tuple[list[Matrix], Matrix]:
    """Return `γ⁰ … γ³` and the metric `η`, over ℚ(i).

    Args:
        representation: `'dirac'` (`γ⁰` diagonal) or `'weyl'` (chiral, `γ⁵` diagonal).
        signature: `'mostly_minus'` (`η = diag(1, -1, -1, -1)`) or `'mostly_plus'` (`η = diag(-1, 1, 1, 1)`,
            the matrices multiplied by `i`).

    Returns:
        The four matrices and `η`.

    Raises:
        CertificateError: If the representation or signature is unknown.

    Examples:
        >>> gammas, eta = gamma_matrices()
        >>> clifford_violations(gammas, eta)
        []
    """
    one, zero = identity_matrix(FIELD, 2), matrix(FIELD, 2, 2)
    if representation == 'dirac':
        gammas = [_block(one, zero, zero, -one)] + [_block(zero, s, -s, zero) for s in PAULI]
    elif representation == 'weyl':
        gammas = [_block(zero, one, one, zero)] + [_block(zero, s, -s, zero) for s in PAULI]
    else:
        message = f"unknown representation {representation!r}; use 'dirac' or 'weyl'"
        raise CertificateError(message)
    eta = matrix(FIELD, 4, 4, lambda i, j: (1 if i == 0 else -1) if i == j else 0)
    if signature == 'mostly_plus':
        gammas, eta = [I * g for g in gammas], -eta
    elif signature != 'mostly_minus':
        message = f"unknown signature {signature!r}; use 'mostly_minus' or 'mostly_plus'"
        raise CertificateError(message)
    return gammas, eta


def gamma5(gammas: Sequence[Matrix], eta: Matrix) -> Matrix:
    """Return `γ⁵`, the product `γ⁰ γ¹ γ² γ³` times `i` or `1`, whichever squares to the identity.

    Args:
        gammas: The gamma matrices.
        eta: The metric (unused: both signatures give `(γ⁰ γ¹ γ² γ³)² = -1`).

    Returns:
        `γ⁵`.

    Examples:
        >>> gammas, eta = gamma_matrices()
        >>> g5 = gamma5(gammas, eta)
        >>> g5 * g5 == 1, all(g5 * g + g * g5 == 0 for g in gammas)
        (True, True)
    """
    del eta
    product = gammas[0] * gammas[1] * gammas[2] * gammas[3]
    return I * product if (I * product) ** 2 == 1 else product


def clifford_violations(gammas: Sequence[Matrix], eta: Matrix) -> list[tuple[int, int]]:
    """Return the index pairs where `{γ^μ, γ^ν} = 2 η^{μν}` fails.

    Args:
        gammas: The gamma matrices.
        eta: The metric.

    Returns:
        The failing pairs.
    """
    one = identity_matrix(FIELD, gammas[0].nrows())
    return [
        (m, n)
        for m, n in itertools.product(range(len(gammas)), repeat=2)
        if gammas[m] * gammas[n] + gammas[n] * gammas[m] != 2 * eta[m, n] * one
    ]


def _gaussian(x: object) -> str:
    """Return an element of ℚ(i) with integer parts as a `GaussianInt` literal."""
    value = FIELD(x)
    a, b = QQ(value[0]), QQ(value[1])
    if a.denominator() != 1 or b.denominator() != 1:
        message = f'{x} is not a Gaussian integer'
        raise CertificateError(message)
    return str(a) if b == 0 else f'⟨{a}, {b}⟩'


def gaussian_matrix_term(m: Matrix) -> str:
    """Return a matrix over ℤ[i] as a Lean `!![…]` literal over `GaussianInt`.

    Args:
        m: The matrix.

    Returns:
        The literal.

    Examples:
        >>> gaussian_matrix_term(PAULI[1])
        '(!![0, ⟨0, -1⟩; ⟨0, 1⟩, 0] : Matrix (Fin 2) (Fin 2) GaussianInt)'
    """
    rows = '; '.join(', '.join(_gaussian(x) for x in row) for row in m.rows())
    return f'(!![{rows}] : Matrix (Fin {m.nrows()}) (Fin {m.ncols()}) GaussianInt)'


def _family(ms: Sequence[Matrix]) -> str:
    """Return matrices as a Lean family `Fin n → Matrix …`."""
    size = ms[0].nrows()
    family = ', '.join(gaussian_matrix_term(m) for m in ms)
    return f'(![{family}] : Fin {len(ms)} → Matrix (Fin {size}) (Fin {size}) GaussianInt)'


def _metric(eta: Matrix) -> str:
    """Return the metric as a Lean `Fin 4 → Fin 4 → GaussianInt`."""
    rows = ', '.join('![' + ', '.join(_gaussian(x) for x in row) + ']' for row in eta.rows())
    return f'(![{rows}] : Fin {eta.nrows()} → Fin {eta.nrows()} → GaussianInt)'


def _fact(name: str, binders: str, body: str, arguments: Sequence[str]) -> str:
    """Return `have name : (fun binders => body) arguments := by decide +kernel`, then its beta-reduced form."""
    return (
        f'have {name} : (fun {binders} => {body}) {" ".join(arguments)} := by\n'
        + '\n'.join(f'  {line}' for line in KERNEL.splitlines())
        + f'\nbeta_reduce at {name}'
    )


def clifford_facts(gammas: Sequence[Matrix], eta: Matrix) -> Lean:
    """Return kernel-checked facts: the Clifford relation, four-gamma traces and two contractions.

    The contractions are `γ^μ γ_μ = 4` and `γ^μ γ^ν γ_μ = -2 γ^ν`.

    Args:
        gammas: The gamma matrices (Sage checks the Clifford relation first).
        eta: The metric.

    Returns:
        The facts `hclifford`, `htrace4`, `hcontract`, `hcontract3`.

    Raises:
        CertificateError: If the Clifford relation fails.
    """
    failures = clifford_violations(gammas, eta)
    if failures:
        message = f'the Clifford relation fails at (μ, ν) = {failures[0]}'
        raise CertificateError(message)
    binders = '(G : Fin 4 → Matrix (Fin 4) (Fin 4) GaussianInt) (η : Fin 4 → Fin 4 → GaussianInt)'
    args = [_family(gammas), _metric(eta)]
    lowered = '∑ μ, η μ μ • (G μ * G μ)'
    facts = [
        _fact('hclifford', binders, '∀ μ ν : Fin 4, G μ * G ν + G ν * G μ = (2 * η μ ν) • 1', args),
        _fact(
            'htrace4',
            binders,
            '∀ μ ν ρ σ : Fin 4, Matrix.trace (G μ * G ν * G ρ * G σ) = '
            '4 * (η μ ν * η ρ σ - η μ ρ * η ν σ + η μ σ * η ν ρ)',
            args,
        ),
        _fact('hcontract', binders, f'{lowered} = (4 : GaussianInt) • 1', args),
        _fact('hcontract3', binders, '∀ ν : Fin 4, ∑ μ, η μ μ • (G μ * G ν * G μ) = (-2 : GaussianInt) • G ν', args),
    ]
    return tactic('\n'.join(facts))


def fierz_basis(gammas: Sequence[Matrix], eta: Matrix) -> tuple[list[Matrix], list[int]]:
    """Return the 16 matrices `1, γ^μ, γ^μ γ^ν (μ < ν), γ^μ γ⁵, γ⁵` and their classes `S, V, T, A, P` (0 … 4).

    `σ^{μν} = (i/2)[γ^μ, γ^ν] = i γ^μ γ^ν` for `μ ≠ ν`; the factor `i` is dropped, which rescales the tensor class.

    Args:
        gammas: The gamma matrices.
        eta: The metric.

    Returns:
        The basis and the class of each element.
    """
    g5 = gamma5(gammas, eta)
    basis = [identity_matrix(FIELD, 4), *gammas]
    basis += [gammas[m] * gammas[n] for m, n in itertools.combinations(range(SPACETIME), 2)]
    basis += [g * g5 for g in gammas] + [g5]
    classes = [0] + [1] * 4 + [2] * 6 + [3] * 4 + [4]
    return basis, classes


def fierz_coefficients(gammas: Sequence[Matrix], eta: Matrix) -> Matrix:
    """Return the 5×5 Fierz matrix `C` with `Σ_{A∈X} (Γ_A)ᵢⱼ (Γ^A)ₖₗ = Σ_Y C_XY Σ_{B∈Y} (Γ_B)ᵢₗ (Γ^B)ₖⱼ`.

    `Γ^A` is the inverse of `Γ_A` (each squares to `±1`).

    Args:
        gammas: The gamma matrices.
        eta: The metric.

    Returns:
        The coefficients.

    Raises:
        CertificateError: If the rearrangement has no solution (the basis is not complete).

    Examples:
        >>> c = fierz_coefficients(*gamma_matrices())
        >>> 4 * c[0]
        (1, 1, 1, 1, 1)
    """
    basis, classes = fierz_basis(gammas, eta)
    inverses = [b.inverse() for b in basis]

    def bilinear(x: int, swap: bool) -> list[object]:
        values = []
        for i, j, k, ell in itertools.product(range(4), repeat=4):
            a, b = (i, ell) if swap else (i, j)
            c, d = (k, j) if swap else (k, ell)
            values.append(sum(basis[n][a, b] * inverses[n][c, d] for n in range(16) if classes[n] == x))
        return values

    targets = [bilinear(y, swap=True) for y in range(5)]
    system = matrix(FIELD, targets).transpose()
    rows = []
    for x in range(5):
        try:
            rows.append(list(system.solve_right(vector(FIELD, bilinear(x, swap=False)))))
        except ValueError:
            message = 'the Fierz rearrangement has no solution in this basis'
            raise CertificateError(message) from None
    return matrix(FIELD, rows)


def fierz_fact(gammas: Sequence[Matrix], eta: Matrix) -> tuple[Matrix, Lean]:
    """Return the Fierz coefficients and a fact proving the rearrangement for every index and class.

    The fact is stated with `4 C` (integers) and checked by the kernel over ℤ[i].

    Args:
        gammas: The gamma matrices.
        eta: The metric.

    Returns:
        `C` and the fact `hfierz`.
    """
    c = fierz_coefficients(gammas, eta)
    basis, classes = fierz_basis(gammas, eta)
    inverses = [b.inverse() for b in basis]
    coefficient = (
        '(!['
        + ', '.join('![' + ', '.join(_gaussian(4 * x) for x in row) + ']' for row in c.rows())
        + '] : Fin 5 → Fin 5 → GaussianInt)'
    )
    class_map = '(![' + ', '.join(str(k) for k in classes) + '] : Fin 16 → Fin 5)'
    binders = (
        '(Γ Γi : Fin 16 → Matrix (Fin 4) (Fin 4) GaussianInt) (cls : Fin 16 → Fin 5) (C : Fin 5 → Fin 5 → GaussianInt)'
    )
    body = (
        '∀ X : Fin 5, ∀ i j k l : Fin 4, '
        '4 * ∑ A ∈ Finset.univ.filter (cls · = X), Γ A i j * Γi A k l = '
        '∑ Y, C X Y * ∑ B ∈ Finset.univ.filter (cls · = Y), Γ B i l * Γi B k j'
    )
    return c, tactic(_fact('hfierz', binders, body, [_family(basis), _family(inverses), class_map, coefficient]))
