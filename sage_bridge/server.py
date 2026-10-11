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
    if len(f.variables()) == 1 and f.degree() == 2:
        fu = f if R.ngens() == 1 else f.univariate_polynomial()
        # a*x^2 + b*x + c = a(x + b/2a)^2 + (c - b^2/4a), both coeffs > 0
        a, b, c = QQ(fu[2]), QQ(fu[1]), QQ(fu[0])
        if a > 0 and b**2 - 4 * a * c < 0:
            x = R(f.variables()[0])
            return [(a, x + b / (2 * a)), (c - b**2 / (4 * a), R.one())]
    raise ValueError(
        f"factor {f} with odd multiplicity is not a supported SOS building block "
        "(supported: constants, single-variable positive-definite quadratics)"
    )


def _sos_from_hints(p, hints, R):
    """Find exact rationals c_0, c_i >= 0 with p = c_0 + sum c_i h_i^2 (hints h_i supplied by the caller).
    Solved exactly: a linear system over the monomials, with an exact rational LP (PPL) if underdetermined."""
    from sage.all import MixedIntegerLinearProgram
    sq = [R.one()] + [h ** 2 for h in hints]
    mons = sorted(set().union(*[set(q.monomials()) for q in sq]) | set(p.monomials()))
    lp = MixedIntegerLinearProgram(solver="PPL", maximization=False)
    c = lp.new_variable(nonnegative=True)
    for m in mons:
        lp.add_constraint(sum(QQ(q.monomial_coefficient(m)) * c[i] for i, q in enumerate(sq)) == QQ(p.monomial_coefficient(m)))
    lp.set_objective(sum(c[i] for i in range(len(sq))))
    try:
        lp.solve()
    except Exception:
        raise ValueError("no nonnegative combination of the hinted squares equals the polynomial")
    vals = [QQ(lp.get_values(c[i])) for i in range(len(sq))]
    if sum(v * q for v, q in zip(vals, sq)) != p:
        raise ValueError("hinted SOS fit is not exact")
    return [(v, (R.one() if i == 0 else hints[i - 1])) for i, v in enumerate(vals) if v != 0]


def do_sos(params):
    """Certify 0 <= poly by an exact decomposition poly = sum c_i * q_i^2."""
    R = _ring(params["vars"])
    p = R(params["poly"])
    if p == 0:
        return {"squares": []}
    if params.get("hints"):
        sos = _sos_from_hints(p, [R(h) for h in params["hints"]], R)
        return {"squares": [{"coeff": str(c), "terms": poly_to_terms(q)} for c, q in sos]}
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


def do_farkas(params):
    """Linear Farkas certificate.  Input: linear polynomials p_i with relations rel_i in {"eq", "le", "lt"}
    meaning p_i = 0, p_i <= 0, p_i < 0.  Output: rationals m_i (m_i >= 0 unless eq) with sum m_i p_i
    identically equal to a constant kappa, where kappa > 0, or kappa = 0 with m_i > 0 on some strict
    relation.  Either way sum m_i p_i <= 0 (resp. < 0) is contradictory.  Solved by exact rational LPs."""
    from sage.all import MixedIntegerLinearProgram
    R = _ring(params["vars"])
    ps = [R(q) for q in params["polys"]]
    rels = params["rels"]
    nonlin = {i for i, q in enumerate(ps) if q.degree() > 1}   # unusable here: forced to multiplier 0
    gens = R.gens()
    def solve(strict_mode):
        lp = MixedIntegerLinearProgram(solver="PPL", maximization=False)
        m = lp.new_variable()
        for i, r in enumerate(rels):
            if i in nonlin:
                lp.add_constraint(m[i] == 0)
            elif r != "eq":
                lp.add_constraint(m[i] >= 0)
        for x in gens:
            lp.add_constraint(sum(QQ(q.monomial_coefficient(x)) * m[i] for i, q in enumerate(ps) if i not in nonlin) == 0)
        kappa = sum(QQ(q.constant_coefficient()) * m[i] for i, q in enumerate(ps) if i not in nonlin)
        if strict_mode:
            if not any(r == "lt" for r in rels):
                return None
            lp.add_constraint(kappa == 0)
            lp.add_constraint(sum(m[i] for i, r in enumerate(rels) if r == "lt") >= 1)
        else:
            lp.add_constraint(kappa >= 1)
        lp.set_objective(sum(m[i] for i, r in enumerate(rels) if r != "eq"))
        try:
            lp.solve()
        except Exception:
            return None
        return [QQ(lp.get_values(m[i])) for i in range(len(ps))]
    for strict_mode in (False, True):
        sol = solve(strict_mode)
        if sol is not None:
            kappa = sum(c * q.constant_coefficient() for c, q in zip(sol, ps))
            strict = any(c != 0 and r == "lt" for c, r in zip(sol, rels))
            return {"multipliers": [str(c) for c in sol], "kappa": str(QQ(kappa)), "strict": bool(strict)}
    raise ValueError("sage_farkas: the linear hypotheses are consistent (no Farkas certificate)")


def do_exists(params):
    """Rational witness for a system: polynomial equations p = 0, linear inequalities p <= 0 / p < 0,
    and disequalities p != 0.  Strategy: solve the equations (linear systems exactly; otherwise Sage's
    solver for rational points), then an exact LP for the linear inequalities, then perturb inside the
    solution set to avoid disequalities.  Returns one rational value per variable."""
    from sage.all import MixedIntegerLinearProgram, matrix, vector
    names = params["vars"]; R = _ring(names); gens = R.gens(); n = len(gens)
    eqs = [R(q) for q in params.get("eqs", [])]
    les = [R(q) for q in params.get("les", [])]
    lts = [R(q) for q in params.get("lts", [])]
    nes = [R(q) for q in params.get("nes", [])]
    lin = all(q.degree() <= 1 for q in eqs + les + lts)
    def ok(pt):
        sub = dict(zip(gens, pt))
        return (all(q.subs(sub) == 0 for q in eqs) and all(q.subs(sub) <= 0 for q in les)
                and all(q.subs(sub) < 0 for q in lts) and all(q.subs(sub) != 0 for q in nes))
    if lin:
        # parametrize the affine solution space of the equations
        A = matrix(QQ, [[QQ(q.monomial_coefficient(x)) for x in gens] for q in eqs]) if eqs else matrix(QQ, 0, n)
        b = vector(QQ, [-QQ(q.constant_coefficient()) for q in eqs]) if eqs else vector(QQ, [])
        x0 = A.solve_right(b) if eqs else vector(QQ, [0] * n)
        K = A.right_kernel().basis_matrix() if eqs else matrix.identity(QQ, n)
        k = K.nrows()
        import itertools
        expr_coeffs = lambda q: (QQ(q.constant_coefficient()) + sum(QQ(q.monomial_coefficient(x)) * x0[j] for j, x in enumerate(gens)),
                                 [sum(QQ(q.monomial_coefficient(x)) * K[r, j] for j, x in enumerate(gens)) for r in range(k)])
        base = [QQ(0)] * k
        if (les or lts) and k > 0:
            lp = MixedIntegerLinearProgram(solver="PPL", maximization=True)
            t = lp.new_variable(); eps = lp.new_variable(nonnegative=True)
            for q in les:
                c0, cs = expr_coeffs(q)
                lp.add_constraint(c0 + sum(cs[r] * t[r] for r in range(k)) <= 0)
            for q in lts:
                c0, cs = expr_coeffs(q)
                lp.add_constraint(c0 + sum(cs[r] * t[r] for r in range(k)) + eps[0] <= 0)
            lp.add_constraint(eps[0] <= 1)
            lp.set_objective(eps[0] if lts else 0)
            try:
                lp.solve()
                base = [QQ(lp.get_values(t[r])) for r in range(k)]
            except Exception:
                raise ValueError("sage_exists: the linear inequalities are infeasible")
        cands = [base]
        for scale in (1, 2, 3, 5, 7, 11):
            for d in itertools.product(range(-1, 2), repeat=min(k, 6)):
                v = list(d) + [0] * (k - min(k, 6))
                cands.append([base[r] + QQ(v[r]) / scale for r in range(k)])
        for c in cands:
            pt = [x0[j] + sum(K[r, j] * c[r] for r in range(k)) for j in range(n)]
            if ok(pt):
                return {"point": [str(QQ(v)) for v in pt]}
        raise ValueError("sage_exists: no rational witness found")
    # nonlinear: rational points of the equations by Sage's solver, filtered by the side conditions
    import sage.all as S
    sv = [S.SR.var(nm) for nm in names]
    res = S.solve([S.SR(str(q)) == 0 for q in eqs], sv, solution_dict=True)
    for sol in res:
        try:
            pt = [QQ(sol[v]) for v in sv]
        except Exception:
            continue
        if ok(pt):
            return {"point": [str(v) for v in pt]}
    raise ValueError("sage_exists: no rational witness found")


METHODS = {
    "ping": lambda params: {"ok": True, "sage": version()},
    "factor": do_factor,
    "sos": do_sos,
    "roots": do_roots,
    "lincomb": do_lincomb,
    "farkas": do_farkas,
    "exists": do_exists,
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
