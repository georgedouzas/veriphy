"""Emit proofs that `VeriphyCheck`'s kernel-evaluated checkers verify, choosing them over entrywise proofs by size."""

from collections.abc import Sequence

from sage.all import QQ, ZZ, Integer, factor, power_mod
from sage.matrix.matrix0 import Matrix

from veriphy.core import CertificateError
from veriphy.toolkit._lean import Lean, tactic, term

ENTRYWISE_LIMIT = 8
BASE_PRIME = 2
DIRECT_LIMIT = 16
KINDS = ('mul', 'bracket', 'commute', 'trace', 'eq')
CHECK_LEMMAS = {
    'mul': 'VeriphyCheck.mul_eq_of_check',
    'bracket': 'VeriphyCheck.bracket_eq_of_check',
    'commute': 'VeriphyCheck.commute_of_check',
    'trace': 'VeriphyCheck.trace_eq_of_check',
    'eq': 'VeriphyCheck.eq_of_check',
}
DECIDABLE_CARRIERS = ('ℤ', 'ℚ', 'ℕ')
ENTRYWISE = 'ext i j\nfin_cases i <;> fin_cases j <;> norm_num'


def matrix_goal_proof(kind: str, size: int, carrier: str, entrywise_limit: int = ENTRYWISE_LIMIT) -> Lean:
    """Return a proof of a matrix goal stated with explicit matrices: entrywise when small, by a checker when large.

    The checker reads the goal's own matrices, so it needs no data from the script. Kernel evaluation needs decidable
    equality of entries, so goals over ℝ or ℂ always get the entrywise proof.

    Args:
        kind: The goal's shape: `mul` (`A * B = C`), `bracket` (`⁅A, B⁆ = C`), `commute` (`A * B = B * A`), `trace`
            (`A.trace = c`) or `eq` (`A = B`).
        size: The matrices' dimension.
        carrier: The type of the entries.
        entrywise_limit: The largest dimension proved entry by entry.

    Returns:
        The tactic.

    Raises:
        CertificateError: If the kind is unknown.

    Examples:
        >>> print(matrix_goal_proof('mul', 2, 'ℚ'))
        ext i j
        fin_cases i <;> fin_cases j <;> norm_num
        >>> print(matrix_goal_proof('commute', 12, 'ℤ'))
        exact VeriphyCheck.commute_of_check (by decide +kernel)
        >>> print(matrix_goal_proof('commute', 12, 'ℝ'))
        ext i j
        fin_cases i <;> fin_cases j <;> norm_num
    """
    if kind not in KINDS:
        message = f'unknown matrix goal kind {kind!r}; use one of {list(KINDS)}'
        raise CertificateError(message)
    if size <= entrywise_limit or carrier not in DECIDABLE_CARRIERS:
        return tactic(ENTRYWISE)
    return tactic(f'exact {CHECK_LEMMAS[kind]} (by decide +kernel)')


def _packing(matrices: Sequence[Matrix]) -> tuple[int, int]:
    """Return the digit width and offset that pack every entry of the matrices as a non-negative digit."""
    largest = ZZ(max((abs(ZZ(x)) for m in matrices for x in m.list()), default=0))
    return max((2 * largest).nbits(), 1), int(largest)


def _packed(m: Matrix, width: int, offset: int) -> str:
    """Return the term listing a matrix's rows, one packed natural number per row."""
    codes = [sum(int(ZZ(x) + offset) << (width * k) for k, x in enumerate(row)) for row in m.rows()]
    return f'VeriphyCheck.unpackRows {width} {offset} {m.nrows()} [{", ".join(map(str, codes))}]'


def packed_product_certificate(a: Matrix, b: Matrix, c: Matrix) -> Lean:
    """Return a proof term of `A * B = C` for large integer matrices, with their rows packed in the certificate.

    The goal's matrices should be definitions (or literals) equal by unfolding to the packed ones; the kernel checks
    the product on lists, at `n³` integer operations.

    Args:
        a: The left factor, an integer matrix.
        b: The right factor.
        c: The claimed product.

    Returns:
        The proof term.

    Raises:
        CertificateError: If the matrices are not square integer matrices of one size, or `a * b != c`.

    Examples:
        >>> from sage.all import matrix
        >>> a, b = matrix(ZZ, [[1, 2], [3, 4]]), matrix(ZZ, [[0, 1], [1, 0]])
        >>> print(packed_product_certificate(a, b, a * b))
        VeriphyCheck.ofLists_mul (n := 2) (rows₁ := VeriphyCheck.unpackRows 4 4 2 [101, 135])
          (rows₂ := VeriphyCheck.unpackRows 4 4 2 [84, 69]) (prod := VeriphyCheck.unpackRows 4 4 2 [86, 120])
          (by decide +kernel) (by decide +kernel)
    """
    n = a.nrows()
    if any(m.nrows() != n or m.ncols() != n for m in (a, b, c)) or any(m.base_ring() != ZZ for m in (a, b, c)):
        message = 'packed certificates take square integer matrices of one size; scale rational ones to integers'
        raise CertificateError(message)
    if a * b != c:
        message = 'the claimed product is wrong: Sage computes a different A * B'
        raise CertificateError(message)
    width, offset = _packing([a, b, c])
    return term(
        f'VeriphyCheck.ofLists_mul (n := {n}) (rows₁ := {_packed(a, width, offset)})\n'
        f'  (rows₂ := {_packed(b, width, offset)}) (prod := {_packed(c, width, offset)})\n'
        '  (by decide +kernel) (by decide +kernel)',
    )


def _pratt_entries(p: Integer, entries: list[tuple[int, int, list[tuple[int, int]]]], seen: set[int]) -> None:
    """Append the Pratt entries certifying `p` (and, first, the primes of `p - 1`)."""
    if p == BASE_PRIME or int(p) in seen:
        return
    factors = [(Integer(q), int(e)) for q, e in factor(p - 1)]
    for q, _ in factors:
        _pratt_entries(q, entries, seen)
    a = 2
    while not (power_mod(a, p - 1, p) == 1 and all(power_mod(a, (p - 1) // q, p) != 1 for q, _ in factors)):
        a += 1
    seen.add(int(p))
    entries.append((int(p), a, [(int(q), e) for q, e in factors]))


def prime_certificate(p: object) -> Lean:
    """Return a proof term of `Nat.Prime p` from a Pratt certificate the kernel checks.

    Args:
        p: A prime number.

    Returns:
        The proof term.

    Raises:
        CertificateError: If `p` is not prime.

    Examples:
        >>> print(prime_certificate(7))
        VeriphyCheck.prime_of_pratt (cert := [(3, 2, [(2, 1)]), (7, 3, [(2, 1), (3, 1)])]) (by decide +kernel)
    """
    prime = Integer(p)
    if not prime.is_prime():
        message = f'{prime} is not prime'
        raise CertificateError(message)
    entries: list[tuple[int, int, list[tuple[int, int]]]] = []
    _pratt_entries(prime, entries, set())
    cert = ', '.join(f'({q}, {a}, [{", ".join(f"({f}, {e})" for f, e in fs)}])' for q, a, fs in entries)
    return term(f'VeriphyCheck.prime_of_pratt (cert := [{cert}]) (by decide +kernel)')


def structure_constants_term(table: Sequence[Sequence[Sequence[object]]]) -> Lean:
    """Return a structure-constant table as a Lean term `Fin n → Fin n → Fin n → ℚ`.

    `VeriphyCheck.jacobi_of_check (by decide +kernel)` and `bracket_self_of_check` then prove the Lie axioms for it.

    Args:
        table: `table[i][j][k]`, the coefficient of `e_k` in `⁅e_i, e_j⁆`, rational.

    Returns:
        The term.

    Examples:
        >>> print(structure_constants_term([[[0, 0], [0, 1]], [[0, -1], [0, 0]]]))
        (![![![0, 0], ![0, 1]], ![![0, -1], ![0, 0]]] : Fin 2 → Fin 2 → Fin 2 → ℚ)
    """
    n = len(table)

    def rat(x: object) -> str:
        q = QQ(x)
        return str(q) if q.denominator() == 1 else f'({q.numerator()} / {q.denominator()})'

    rows = ', '.join('![' + ', '.join('![' + ', '.join(rat(x) for x in r) + ']' for r in m) + ']' for m in table)
    return term(f'(![{rows}] : Fin {n} → Fin {n} → Fin {n} → ℚ)')
