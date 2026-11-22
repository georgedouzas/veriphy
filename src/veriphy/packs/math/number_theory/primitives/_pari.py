"""Check number-theoretic claims with PARI/GP, as Sage ships it: a factorization, and a number field's class number.

These functions run under Sage, through the math pack's `sage` tool.
"""

import re

TERM = re.compile(r'^(\d+)(?:\s*\^\s*(\d+))?$')


def _tools() -> list[dict[str, str]]:
    """Return PARI's version, as a record names it."""
    from sage.libs.pari import pari  # noqa: PLC0415 - runs under Sage only

    major, minor, patch = (int(v) for v in pari.version()[:3])
    return [{'name': 'pari', 'version': f'{major}.{minor}.{patch}', 'pin': 'version'}]


def factorization(inputs: dict[str, object]) -> dict[str, object]:
    """Check a claimed factorization into primes: that the factors multiply to the number and that each is prime.

    Primality is PARI's `isprime`, which proves it (APR-CL or ECPP) rather than testing it.

    Args:
        inputs: `number`, an integer, and `claimed`, its factorization, as `2^3 * 3 * 5` (a prime is its own).

    Returns:
        `accepted` when the claim is the number's factorization into primes, `refused` with what is wrong otherwise,
        and PARI's factorization.
    """
    from sage.libs.pari import pari  # noqa: PLC0415 - runs under Sage only

    number = int(str(inputs['number']))
    terms = [TERM.match(t.strip()) for t in str(inputs['claimed']).replace('·', '*').split('*')]
    if not all(terms):
        return {'status': 'failed', 'error': 'write the factorization as a product of primes and powers: 2^3 * 3 * 5'}
    factors = [(int(m[1]), int(m[2] or 1)) for m in terms if m]
    found = pari(number).factor()
    shown = ' * '.join(f'{p}^{e}' if e > 1 else f'{p}' for p, e in zip(found[0], found[1], strict=True))
    errors = [f'{p} is not prime' for p, _ in factors if not pari(p).isprime()]
    product = 1
    for prime, exponent in factors:
        product *= prime**exponent
    if product != number:
        errors.append(f'the factors multiply to {product}, not {number}')
    status = 'refused' if errors else 'accepted'
    return {'status': status, 'factorization': shown, 'errors': [{'message': e} for e in errors], 'tools': _tools()}


def class_number(inputs: dict[str, object]) -> dict[str, object]:
    """Compute the class number of the number field a polynomial defines, certified, and compare the claim with it.

    `bnfinit` assumes the generalized Riemann hypothesis; `bnfcertify` then removes the assumption, so an accepted
    claim holds unconditionally.

    Args:
        inputs: `polynomial`, irreducible in `x`, such as `x^2 + 5`, and `claimed`, the class number.

    Returns:
        `accepted` or `refused`, with the class number and the field's discriminant, or `undecided` when PARI cannot
        certify it.
    """
    from sage.libs.pari import pari  # noqa: PLC0415 - runs under Sage only

    polynomial = pari(str(inputs['polynomial']))
    if not polynomial.polisirreducible():
        return {'status': 'failed', 'error': f'{polynomial} is not irreducible, so it defines no number field'}
    field = polynomial.bnfinit(1)
    number, discriminant = int(field.bnf_get_no()), int(polynomial.nfdisc())
    found = {'class_number': number, 'discriminant': discriminant, 'tools': _tools()}
    if int(field.bnfcertify()) != 1:
        return found | {'status': 'undecided', 'error': 'PARI could not certify the class group without GRH'}
    claimed = int(str(inputs['claimed']))
    if claimed != number:
        return found | {'status': 'refused', 'errors': [{'message': f'the class number is {number}, not {claimed}'}]}
    return found | {'status': 'accepted'}
