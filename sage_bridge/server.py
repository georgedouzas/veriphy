"""Veriphy Sage bridge daemon.

JSON-RPC over stdio: one request object per line on stdin, one response per
line on stdout. Run with `sage -python server.py`.

The daemon is an UNTRUSTED oracle. Every method returns a certificate that the
Lean side must reconstruct into a kernel-checked proof; nothing here is part of
the trusted base. Polynomials cross the boundary as structured term lists
(coefficient + exponent vector), never as syntax strings.

Methods:
  ping                                   -> {"ok": true, "sage": <version>}
  factor {poly: str, vars: [str]}        -> {"unit": str, "factors": [{"terms": [...], "mult": int}]}

Term list encoding of a polynomial in QQ[vars]:
  [{"coeff": "<rational as num or num/den>", "exps": [e1, e2, ...]}, ...]
where exps[i] is the exponent of vars[i] in that monomial.

Four methods are ADVISORY, not certificate-producing: `symbolic_check` (is
this identity symbolically true? for the formalization-time lie detector),
`matrix_check` (the same decision for matrix-valued identities — Clifford
relations, representation identities, determinant formulas), `solve` (symbolic
solution sets, as proof-sketch guidance) and `run_script` (a whole derivation
session — loops, random trials, Lean-syntax generation — returning a
structured `results` dict). Their results are marked "advisory": they must
never be transcribed into a proof — the Lean side re-proves anything it uses
from them. `run_script` executes arbitrary Sage code with the daemon's own
privileges; that is deliberate — the daemon is an untrusted, user-launched
oracle, and Veriphy's trust boundary is the Lean kernel, not this process.
"""

import json
import sys

from sage.all import QQ, PolynomialRing, version


def poly_to_terms(p):
    """Encode a multivariate polynomial over QQ as a JSON-safe term list."""
    terms = []
    for exps, coeff in sorted(p.dict().items()):
        # exps is an int (univariate) or an ETuple (multivariate)
        exps = tuple(exps) if hasattr(exps, "__iter__") else (exps,)
        terms.append({"coeff": str(QQ(coeff)), "exps": [int(e) for e in exps]})
    return terms


def do_factor(params):
    names = params["vars"]
    if not names or not all(n.isidentifier() for n in names):
        raise ValueError("vars must be non-empty valid identifiers")
    R = PolynomialRing(QQ, names)
    p = R(params["poly"])
    fac = p.factor()
    return {
        "unit": str(QQ(fac.unit())),
        "factors": [{"terms": poly_to_terms(q), "mult": int(m)} for q, m in fac],
    }


def _ring(names):
    if not names or not all(n.isidentifier() for n in names):
        raise ValueError("vars must be non-empty valid identifiers")
    return PolynomialRing(QQ, names)


def _sos_mul(A, B):
    """Product of two SOS lists: (Σ cᵢqᵢ²)(Σ dⱼrⱼ²) = Σᵢⱼ (cᵢdⱼ)(qᵢrⱼ)²."""
    return [(c * d, q * r) for (c, q) in A for (d, r) in B]


def _sos_of_irreducible(f, R):
    """SOS list for one irreducible factor, or raise if not expressible."""
    if f.degree() == 0:
        c = QQ(f)
        if c < 0:
            raise ValueError(f"negative constant factor {c}")
        return [(c, R.one())]
    fu = f if R.ngens() == 1 else f.univariate_polynomial()
    if len(f.variables()) == 1 and f.degree() == 2:
        # a*x^2 + b*x + c = a(x + b/2a)^2 + (c - b^2/4a), both coeffs > 0
        a, b, c = QQ(fu[2]), QQ(fu[1]), QQ(fu[0])
        if a > 0 and b**2 - 4 * a * c < 0:
            x = R(f.variables()[0])
            return [(a, x + b / (2 * a)), (c - b**2 / (4 * a), R.one())]
    raise ValueError(
        f"factor {f} with odd multiplicity is not a supported SOS building block "
        "(supported: constants, single-variable positive-definite quadratics)"
    )


def do_sos(params):
    """Certify 0 <= poly by an exact decomposition poly = sum c_i * q_i^2."""
    R = _ring(params["vars"])
    p = R(params["poly"])
    if p == 0:
        return {"squares": []}
    fac = p.factor()
    unit = QQ(fac.unit())
    if unit < 0:
        raise ValueError(f"negative leading unit {unit}: polynomial is not SOS")
    sos = [(unit, R.one())]
    for f, m in fac:
        half, odd = divmod(m, 2)
        if half:
            sos = _sos_mul(sos, [(QQ(1), f**half)])
        if odd:
            sos = _sos_mul(sos, _sos_of_irreducible(f, R))
    return {"squares": [{"coeff": str(c), "terms": poly_to_terms(q)} for c, q in sos]}


def do_roots(params):
    """Rational roots of a univariate polynomial over QQ."""
    R = PolynomialRing(QQ, params["var"])
    p = R(params["poly"])
    return {"roots": [str(QQ(r)) for r, _ in p.roots(QQ)]}


def do_lincomb(params):
    """Ideal-membership certificate: cofactors c_i with target = sum c_i * hyp_i."""
    names = params["vars"]
    if not names or not all(n.isidentifier() for n in names):
        raise ValueError("vars must be non-empty valid identifiers")
    R = PolynomialRing(QQ, len(names), names)  # force multivariate: lift needs it
    target = R(params["target"])
    hyps = [R(h) for h in params["hyps"]]
    cofactors = target.lift(R.ideal(hyps))
    return {"cofactors": [poly_to_terms(c) for c in cofactors]}


def do_sum(params):
    """Closed form of sum(f(k), k, 0, n-1) as a polynomial in n over QQ."""
    from sage.all import SR, var

    k, n = var("k"), var("n")
    f = SR(params["summand"])
    if set(f.variables()) - {k}:
        raise ValueError("summand may only contain the variable k")
    S = f.sum(k, 0, n - 1)
    p = S.expand().polynomial(QQ)
    return {"closed_form": poly_to_terms(p), "var": "n"}


def _symbolic_exprs(strs, names):
    """Parse expression strings in the symbolic ring with the declared variables.

    Each string is an expression, an equation (`lhs == rhs`), or a relation
    (`x > 0`). Parsed with sage_eval, so the full Sage expression language is
    available — acceptable for ADVISORY methods only.
    """
    from sage.all import sage_eval, var

    if not names or not all(n.isidentifier() for n in names):
        raise ValueError("vars must be non-empty valid identifiers")
    scope = {n: var(n) for n in names}
    return [sage_eval(s, locals=scope) for s in strs]


def do_symbolic_check(params):
    """ADVISORY: decide whether `lhs == rhs` as a symbolic identity.

    Tries full symbolic simplification first; falls back to numeric sampling.
    Returns {"equal": true|false|null, "method": ..., "advisory": true} plus a
    counterexample when sampling refutes the identity. `null` means undecided:
    simplification did not reach zero but no sampled point refuted it.
    """
    import random

    from sage.all import CDF, assume, forget, var

    names = params["vars"]
    lhs, rhs = _symbolic_exprs([params["lhs"], params["rhs"]], names)
    assumptions = _symbolic_exprs(params.get("assumptions", []), names)
    try:
        for a in assumptions:
            assume(a)
        diff = (lhs - rhs).simplify_full()
        if diff.is_zero():
            return {"equal": True, "method": "symbolic", "advisory": True}
        # Numeric fallback on the UNsimplified difference, at random real points.
        samples = int(params.get("samples", 20))
        tol = 1e-8
        tried = 0
        for _ in range(10 * samples):
            if tried >= samples:
                break
            point = {var(v): random.uniform(-10, 10) for v in names}
            try:
                val = CDF((lhs - rhs).subs(point))
            except (ValueError, TypeError, ZeroDivisionError, ArithmeticError):
                continue  # outside the domain; resample
            tried += 1
            if abs(val) > tol:
                return {
                    "equal": False,
                    "method": "numeric",
                    "advisory": True,
                    "counterexample": {str(v): float(x) for v, x in point.items()},
                    "difference": str(val),
                }
        if tried == 0:
            raise ValueError("no sample point evaluated successfully")
        return {
            "equal": None,
            "method": "numeric",
            "advisory": True,
            "note": f"undecided symbolically; {tried} random samples found no counterexample",
        }
    finally:
        forget()


def do_solve(params):
    """ADVISORY: symbolic solution set of an equation system, as proof guidance.

    Equations are strings (`lhs == rhs`, or an expression meaning `expr == 0`).
    Solutions come back as {var: expression-string} dicts; free parameters keep
    Sage's names (r1, z1, ...). Guidance only — re-prove everything in Lean.
    """
    from sage.all import SR, solve, var

    names = params["vars"]
    eqs = [
        e if e.is_relational() else (e == 0)
        for e in _symbolic_exprs(params["equations"], names)
    ]
    unknowns = [var(v) for v in params.get("solve_for", names)]
    sols = solve(eqs, unknowns, solution_dict=True)
    return {
        "solutions": [{str(v): str(e) for v, e in s.items()} for s in sols],
        "advisory": True,
    }


def do_matrix_check(params):
    """ADVISORY: decide a matrix-valued (or scalar) identity `lhs == rhs`.

    `matrices` maps names to rectangular arrays of entry strings (symbolic
    expressions in the declared `vars`); `lhs` and `rhs` are Sage expressions
    over those names, the scalar vars and the full Sage language (so
    `A * B + B * A`, `(gamma1 * X).det()`, `identity_matrix(4)` all work).
    Decision mirrors `symbolic_check`: entrywise symbolic simplification
    first, then numeric sampling with a counterexample on refutation; `null`
    means undecided.
    """
    import random

    from sage.all import CDF, SR, assume, forget, matrix, sage_eval, var

    names = params.get("vars", [])
    if not all(n.isidentifier() for n in names):
        raise ValueError("vars must be valid identifiers")
    scope = {n: var(n) for n in names}
    for mname, rows in params.get("matrices", {}).items():
        if not mname.isidentifier():
            raise ValueError(f"matrix name {mname!r} is not a valid identifier")
        entries = [[sage_eval(str(e), locals=dict(scope)) for e in row] for row in rows]
        scope[mname] = matrix(SR, entries)
    lhs = sage_eval(params["lhs"], locals=dict(scope))
    rhs = sage_eval(params["rhs"], locals=dict(scope))
    assumptions = _symbolic_exprs(params.get("assumptions", []), names) if names else []
    try:
        for a in assumptions:
            assume(a)
        diff = lhs - rhs
        entries = list(diff.list()) if hasattr(diff, "nrows") else [SR(diff)]
        if all(SR(e).simplify_full().is_zero() for e in entries):
            return {"equal": True, "method": "symbolic", "advisory": True}
        samples = int(params.get("samples", 20))
        tol = 1e-8
        tried = 0
        for _ in range(10 * samples):
            if tried >= samples:
                break
            point = {var(v): random.uniform(-10, 10) for v in names}
            try:
                vals = [CDF(SR(e).subs(point)) for e in entries]
            except (ValueError, TypeError, ZeroDivisionError, ArithmeticError):
                continue  # outside the domain; resample
            tried += 1
            worst = max(abs(v) for v in vals)
            if worst > tol:
                return {
                    "equal": False,
                    "method": "numeric",
                    "advisory": True,
                    "counterexample": {str(v): float(x) for v, x in point.items()},
                    "max_entry_difference": str(worst),
                }
        if tried == 0:
            if not names:
                raise ValueError("entries did not simplify to zero and there "
                                 "are no vars to sample")
            raise ValueError("no sample point evaluated successfully")
        return {
            "equal": None,
            "method": "numeric",
            "advisory": True,
            "note": f"undecided symbolically; {tried} random samples found no counterexample",
        }
    finally:
        forget()


def _json_safe(x, depth=0):
    """Best-effort conversion of Sage values to JSON-safe structures."""
    if depth > 6:
        return str(x)
    if x is None or isinstance(x, (bool, int, float, str)):
        return x
    if isinstance(x, (list, tuple)):
        return [_json_safe(v, depth + 1) for v in x]
    if isinstance(x, dict):
        return {str(k): _json_safe(v, depth + 1) for k, v in x.items()}
    return str(x)


def do_run_script(params):
    """ADVISORY: run a whole Sage derivation script, as one oracle session.

    The script is preparsed Sage source (loops, defs, random trials, printing
    Lean-ready tables). It communicates structured findings by assigning a
    JSON-safe dict to a top-level variable named `results`; everything it
    prints comes back as `stdout` (truncated beyond 20000 chars). A
    `timeout_s` (default 120) bounds the run via SIGALRM. Guidance only —
    whatever the script discovers must be re-proved in Lean.
    """
    import contextlib
    import io
    import signal

    from sage.repl.preparse import preparse_file

    script = params["script"]
    timeout = int(params.get("timeout_s", 120))
    ns = {}
    exec("from sage.all import *", ns)  # noqa: S102 — untrusted-oracle boundary
    code = compile(preparse_file(script), "<veriphy-script>", "exec")
    buf = io.StringIO()

    def _on_alarm(signum, frame):
        raise TimeoutError(f"script exceeded {timeout}s")

    old_handler = signal.signal(signal.SIGALRM, _on_alarm)
    signal.alarm(timeout)
    try:
        with contextlib.redirect_stdout(buf):
            exec(code, ns)  # noqa: S102 — untrusted-oracle boundary
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
    out = buf.getvalue()
    if len(out) > 20000:
        out = out[:20000] + f"\n...[truncated {len(out) - 20000} chars]"
    return {
        "results": _json_safe(ns.get("results")),
        "stdout": out,
        "advisory": True,
    }


METHODS = {
    "ping": lambda params: {"ok": True, "sage": version()},
    "factor": do_factor,
    "sos": do_sos,
    "roots": do_roots,
    "lincomb": do_lincomb,
    "sum": do_sum,
    "symbolic_check": do_symbolic_check,
    "matrix_check": do_matrix_check,
    "solve": do_solve,
    "run_script": do_run_script,
}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        req_id = None
        try:
            req = json.loads(line)
            req_id = req.get("id")
            method = METHODS[req["method"]]
            resp = {"id": req_id, "result": method(req.get("params", {}))}
        except Exception as exc:  # report, keep serving
            resp = {"id": req_id, "error": f"{type(exc).__name__}: {exc}"}
        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
