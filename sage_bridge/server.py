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

Adding a method: decorate it with `@method(name, **params)`. Each keyword names
a request parameter and its coercer (`Vars` builds the ring `R`, `Poly` parses
in it, ...); the body receives the coerced values, returns plain Sage values,
and `encode` turns rationals into exact strings and polynomials into term lists.
Any exception becomes the error response `<method>: <reason>`.

Four methods are ADVISORY, not certificate-producing: `symbolic_check` (is
this identity symbolically true? for the formalization-time lie detector),
`matrix_check` (the same decision for matrix-valued identities — Clifford
relations, representation identities, determinant formulas), `solve` (symbolic
solution sets, as proof-sketch guidance) and `run_script` (a whole derivation
session — loops, random trials, Lean-syntax generation — returning a
structured `results` dict). Their results are marked "advisory": they must
never be transcribed into a proof — the Lean side re-proves anything it uses
from them. `run_script` and `certify` execute arbitrary Sage code with the
daemon's own privileges; that is deliberate — the daemon is an untrusted,
user-launched oracle, and Veriphy's trust boundary is the Lean kernel, not this
process.
"""

import json
import sys
from collections import namedtuple

from sage.all import QQ, ZZ, PolynomialRing, version
from sage.rings.polynomial.multi_polynomial import MPolynomial
from sage.rings.polynomial.polynomial_element import Polynomial
from sage.structure.element import Element

# --------------------------------------------------------------------------
# Method framework: registration, parameter coercion, exact encoding, errors
# --------------------------------------------------------------------------

METHODS = {}

RELATIONS = ("eq", "le", "lt", "ne")


class ParamError(ValueError):
    """A request parameter failed validation; the message names the parameter."""

    def __init__(self, param, why):
        super().__init__(f"parameter '{param}': {why}")
        self.param = param


def poly_to_terms(p):
    """Encode a multivariate polynomial over QQ as a JSON-safe term list."""
    terms = []
    for exps, coeff in sorted(p.dict().items()):
        # exps is an int (univariate) or an ETuple (multivariate)
        exps = tuple(exps) if hasattr(exps, "__iter__") else (exps,)
        terms.append({"coeff": str(QQ(coeff)), "exps": [int(e) for e in exps]})
    return terms


def encode(x, advisory=False, depth=0):
    """Exact JSON encoding of a method result: rationals as "n" / "n/d" strings, polynomials as term
    lists, containers recursively. Certificate methods may not return floats or opaque objects;
    advisory methods fall back to `str`."""
    if depth > 12:
        if advisory:
            return str(x)
        raise TypeError("result nested too deeply")
    if x is None or isinstance(x, (bool, str)):
        return x
    if isinstance(x, int):
        return x  # Python ints are structural (exponents, multiplicities, counts)
    if isinstance(x, float):
        if advisory:
            return x
        raise TypeError(f"floating-point value {x} in a certificate result")
    if isinstance(x, (list, tuple)):
        return [encode(v, advisory, depth + 1) for v in x]
    if isinstance(x, dict):
        return {str(k): encode(v, advisory, depth + 1) for k, v in x.items()}
    if isinstance(x, (MPolynomial, Polynomial)):
        return poly_to_terms(x)
    if isinstance(x, Element) and x.parent() in (QQ, ZZ):
        return str(x)  # exact only: never rationalize a floating-point Sage real
    if advisory:
        return str(x)
    raise TypeError(f"cannot encode {type(x).__name__} exactly")


def method(name, advisory=False, raw=False, **params):
    """Register a daemon method. Keyword arguments map request parameters to coercers, applied in
    declaration order with a shared context (so `Poly` sees the ring `Vars` built). With `raw=True`
    the body receives the params dict untouched (advisory methods with free-form inputs)."""

    def deco(fn):
        def run(req_params):
            req_params = req_params or {}
            try:
                if raw:
                    out = fn(req_params)
                else:
                    ctx, kwargs = {}, {}
                    for pname, coerce in params.items():
                        key, value = coerce(pname, req_params, ctx)
                        kwargs[key] = value
                    out = fn(**kwargs)
                return encode(out, advisory)
            except ParamError as exc:
                raise MethodError(f"{name}: {exc}") from exc
            except MethodError:
                raise
            except ValueError as exc:
                raise MethodError(f"{name}: {exc}") from exc
            except Exception as exc:  # report every failure on the same line protocol
                raise MethodError(f"{name}: {type(exc).__name__}: {exc}") from exc

        run.__name__ = fn.__name__
        run.__doc__ = fn.__doc__
        run.advisory = advisory
        METHODS[name] = run
        return run

    return deco


class MethodError(Exception):
    """A method failed; the message is already `<method>: <reason>`."""


def _get(pname, req, default=...):
    if pname in req:
        return req[pname]
    if default is not ...:
        return default
    raise ParamError(pname, "missing")


def Vars(pname, req, ctx):
    """Non-empty list of identifiers -> the ring QQ[vars] (always multivariate; passed as `R`)."""
    names = _get(pname, req)
    if not isinstance(names, list) or not names:
        raise ParamError(pname, "must be a non-empty list of identifiers")
    bad = [n for n in names if not isinstance(n, str) or not n.isidentifier()]
    if bad:
        raise ParamError(pname, f"not valid identifiers: {bad}")
    ctx["R"] = PolynomialRing(QQ, len(names), names)
    return "R", ctx["R"]


def UniVar(pname, req, ctx):
    """One identifier -> the univariate ring QQ[var] (passed as `R`)."""
    v = _get(pname, req)
    if not isinstance(v, str) or not v.isidentifier():
        raise ParamError(pname, "must be an identifier")
    ctx["R"] = PolynomialRing(QQ, v)
    return "R", ctx["R"]


def _parse_poly(pname, s, ctx):
    R = ctx.get("R")
    if R is None:
        raise ParamError(pname, "declared before the variables")
    if not isinstance(s, str):
        raise ParamError(pname, "must be a polynomial string")
    try:
        return R(s)
    except Exception as exc:
        raise ParamError(pname, f"not a polynomial in QQ[{', '.join(map(str, R.gens()))}]: {s!r} ({exc})")


def Poly(pname, req, ctx):
    return pname, _parse_poly(pname, _get(pname, req), ctx)


def PolyList(pname, req, ctx):
    xs = _get(pname, req, [])
    if not isinstance(xs, list):
        raise ParamError(pname, "must be a list of polynomial strings")
    return pname, [_parse_poly(pname, s, ctx) for s in xs]


def RelList(*allowed):
    allowed = allowed or RELATIONS

    def coerce(pname, req, ctx):
        xs = _get(pname, req)
        if not isinstance(xs, list) or any(r not in allowed for r in xs):
            raise ParamError(pname, f"must be a list of relations in {list(allowed)}")
        return pname, xs

    return coerce


def Str(pname, req, ctx):
    s = _get(pname, req)
    if not isinstance(s, str):
        raise ParamError(pname, "must be a string")
    return pname, s


def Int(default):
    def coerce(pname, req, ctx):
        v = _get(pname, req, default)
        try:
            return pname, int(v)
        except (TypeError, ValueError):
            raise ParamError(pname, "must be an integer")

    return coerce


def Json(pname, req, ctx):
    return pname, _get(pname, req)


# --------------------------------------------------------------------------
# Shared exact solvers
# --------------------------------------------------------------------------


def exact_lp(nvars, eqs=(), les=(), objective=None, nonneg=False, maximize=False):
    """Exact rational LP over variables t_0 .. t_{nvars-1}.

    Rows are `(coeffs, const)` meaning `sum coeffs[j] t_j + const` (= 0 for `eqs`, <= 0 for `les`);
    `nonneg` is True (all variables) or an iterable of indices; `objective` is a coefficient list.
    Returns a list of QQ, or None when infeasible (or unbounded). Never hands PPL an empty problem:
    no variables, or constant rows, are decided directly."""
    from sage.all import MixedIntegerLinearProgram
    from sage.numerical.mip import MIPSolverException

    nn = set(range(nvars)) if nonneg is True else set(nonneg or ())
    live_eqs, live_les = [], []
    for rows, live, sat in ((eqs, live_eqs, lambda c: c == 0), (les, live_les, lambda c: c <= 0)):
        for coeffs, const in rows:
            coeffs = [QQ(c) for c in coeffs]
            if any(coeffs):
                live.append((coeffs, QQ(const)))
            elif not sat(QQ(const)):
                return None  # a constant row that is false: infeasible
    if nvars == 0 or not (live_eqs or live_les):
        return [QQ(0)] * nvars  # nothing left to satisfy: the zero point is feasible
    lp = MixedIntegerLinearProgram(solver="PPL", maximization=maximize)
    t = lp.new_variable()
    for j in nn:
        lp.add_constraint(t[j] >= 0)
    lin = lambda cs: lp.sum(c * t[j] for j, c in enumerate(cs) if c != 0)
    for cs, c0 in live_eqs:
        lp.add_constraint(lin(cs) == -c0)
    for cs, c0 in live_les:
        lp.add_constraint(lin(cs) <= -c0)
    if objective is not None and any(QQ(c) != 0 for c in objective):
        lp.set_objective(lin([QQ(c) for c in objective]))
    else:
        lp.set_objective(None)
    try:
        lp.solve()
    except MIPSolverException:
        return None
    return [QQ(lp.get_values(t[j])) for j in range(nvars)]


# --------------------------------------------------------------------------
# Certificate methods
# --------------------------------------------------------------------------

method("ping", raw=True)(lambda params: {"ok": True, "sage": version()})


@method("factor", vars=Vars, poly=Poly)
def do_factor(R, poly):
    fac = poly.factor()
    return {
        "unit": QQ(fac.unit()),
        "factors": [{"terms": q, "mult": int(m)} for q, m in fac],
    }


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
        fu = f.univariate_polynomial()
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
    """Find exact rationals c_0, c_i >= 0 with p = c_0 + sum c_i h_i^2 (hints h_i supplied by the caller):
    one equality per monomial, minimal total weight, by the exact LP."""
    sq = [R.one()] + [h ** 2 for h in hints]
    mons = sorted(set().union(*[set(q.monomials()) for q in sq]) | set(p.monomials()))
    rows = [([q.monomial_coefficient(m) for q in sq], -p.monomial_coefficient(m)) for m in mons]
    vals = exact_lp(len(sq), eqs=rows, objective=[1] * len(sq), nonneg=True)
    if vals is None:
        raise ValueError("no nonnegative combination of the hinted squares equals the polynomial")
    if sum(v * q for v, q in zip(vals, sq)) != p:
        raise ValueError("hinted SOS fit is not exact")
    return [(v, (R.one() if i == 0 else hints[i - 1])) for i, v in enumerate(vals) if v != 0]


@method("sos", vars=Vars, poly=Poly, hints=PolyList)
def do_sos(R, poly, hints):
    """Certify 0 <= poly by an exact decomposition poly = sum c_i * q_i^2."""
    p = poly
    if p == 0:
        return {"squares": []}
    if hints:
        sos = _sos_from_hints(p, hints, R)
    else:
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
    return {"squares": [{"coeff": c, "terms": q} for c, q in sos]}


@method("roots", var=UniVar, poly=Poly)
def do_roots(R, poly):
    """Rational roots of a univariate polynomial over QQ."""
    return {"roots": [QQ(r) for r, _ in poly.roots(QQ)]}


@method("lincomb", vars=Vars, target=Poly, hyps=PolyList)
def do_lincomb(R, target, hyps):
    """Ideal-membership certificate: cofactors c_i with target = sum c_i * hyp_i."""
    if not hyps:
        raise ParamError("hyps", "no hypotheses to combine")
    return {"cofactors": list(target.lift(R.ideal(hyps)))}


@method("sum", summand=Str)
def do_sum(summand):
    """Closed form of sum(f(k), k, 0, n-1) as a polynomial in n over QQ."""
    from sage.all import SR, var

    k, n = var("k"), var("n")
    try:
        f = SR(summand)
    except Exception as exc:
        raise ParamError("summand", str(exc))
    if set(f.variables()) - {k}:
        raise ParamError("summand", "may only contain the variable k")
    S = f.sum(k, 0, n - 1)
    return {"closed_form": S.expand().polynomial(QQ), "var": "n"}


@method("farkas", vars=Vars, polys=PolyList, rels=RelList("eq", "le", "lt"))
def do_farkas(R, polys, rels):
    """Linear Farkas certificate.  Input: linear polynomials p_i with relations rel_i in {"eq", "le", "lt"}
    meaning p_i = 0, p_i <= 0, p_i < 0.  Output: rationals m_i (m_i >= 0 unless eq) with sum m_i p_i
    identically equal to a constant kappa, where kappa > 0, or kappa = 0 with m_i > 0 on some strict
    relation.  Either way sum m_i p_i <= 0 (resp. < 0) is contradictory.  Solved by exact rational LPs."""
    ps = polys
    if len(rels) != len(ps):
        raise ParamError("rels", f"expected {len(ps)} relations, got {len(rels)}")
    n = len(ps)
    nonlin = {i for i, q in enumerate(ps) if q.degree() > 1}   # unusable here: forced to multiplier 0
    unit = lambda i: [1 if j == i else 0 for j in range(n)]
    nonneg = [i for i, r in enumerate(rels) if r != "eq"]
    base_eqs = [(unit(i), 0) for i in nonlin]
    for x in R.gens():
        base_eqs.append(([0 if i in nonlin else q.monomial_coefficient(x) for i, q in enumerate(ps)], 0))
    kappa = [0 if i in nonlin else q.constant_coefficient() for i, q in enumerate(ps)]
    weight = [0 if r == "eq" else 1 for r in rels]
    strict = [1 if r == "lt" else 0 for r in rels]
    attempts = [(base_eqs, [([-c for c in kappa], 1)])]          # kappa >= 1
    if any(strict):
        attempts.append((base_eqs + [(kappa, 0)], [([-s for s in strict], 1)]))  # kappa = 0, strict weight >= 1
    for eqs, les in attempts:
        sol = exact_lp(n, eqs=eqs, les=les, objective=weight, nonneg=nonneg)
        if sol is not None:
            k = sum(c * q.constant_coefficient() for c, q in zip(sol, ps))
            return {"multipliers": sol, "kappa": QQ(k),
                    "strict": bool(any(c != 0 and r == "lt" for c, r in zip(sol, rels)))}
    raise ValueError("the linear hypotheses are consistent (no Farkas certificate)")


@method("exists", vars=Vars, eqs=PolyList, les=PolyList, lts=PolyList, nes=PolyList)
def do_exists(R, eqs, les, lts, nes):
    """Rational witness for a system: polynomial equations p = 0, linear inequalities p <= 0 / p < 0,
    and disequalities p != 0.  Strategy: solve the equations (linear systems exactly; otherwise Sage's
    solver for rational points), then an exact LP for the linear inequalities, then perturb inside the
    solution set to avoid disequalities.  Returns one rational value per variable."""
    import itertools

    from sage.all import matrix, vector

    gens = R.gens(); n = len(gens)
    lin = all(q.degree() <= 1 for q in eqs + les + lts)

    def ok(pt):
        sub = dict(zip(gens, pt))
        return (all(q.subs(sub) == 0 for q in eqs) and all(q.subs(sub) <= 0 for q in les)
                and all(q.subs(sub) < 0 for q in lts) and all(q.subs(sub) != 0 for q in nes))

    if lin:
        # parametrize the affine solution space of the equations: x = x0 + t K
        A = matrix(QQ, [[QQ(q.monomial_coefficient(x)) for x in gens] for q in eqs]) if eqs else matrix(QQ, 0, n)
        b = vector(QQ, [-QQ(q.constant_coefficient()) for q in eqs]) if eqs else vector(QQ, [])
        try:
            x0 = A.solve_right(b) if eqs else vector(QQ, [0] * n)
        except ValueError:
            raise ValueError("the equations are inconsistent")
        K = A.right_kernel().basis_matrix() if eqs else matrix.identity(QQ, n)
        k = K.nrows()

        def in_t(q):  # q(x0 + t K) as (coefficients in t, constant)
            c0 = QQ(q.constant_coefficient()) + sum(QQ(q.monomial_coefficient(x)) * x0[j] for j, x in enumerate(gens))
            cs = [sum(QQ(q.monomial_coefficient(x)) * K[r, j] for j, x in enumerate(gens)) for r in range(k)]
            return cs, c0

        base = [QQ(0)] * k
        if les or lts:
            # variables t_0..t_{k-1} (free) and eps = t_k in [0, 1]; maximize eps for the strict rows
            rows = [(cs + [0], c0) for cs, c0 in map(in_t, les)]
            rows += [(cs + [1], c0) for cs, c0 in map(in_t, lts)]
            rows.append(([0] * k + [1], -1))
            sol = exact_lp(k + 1, les=rows, objective=[0] * k + [1], nonneg=[k], maximize=True)
            if sol is None:
                raise ValueError("the linear inequalities are infeasible")
            base = sol[:k]
        cands = [base]
        for scale in (1, 2, 3, 5, 7, 11):
            for d in itertools.product(range(-1, 2), repeat=min(k, 6)):
                v = list(d) + [0] * (k - min(k, 6))
                cands.append([base[r] + QQ(v[r]) / scale for r in range(k)])
        for c in cands:
            pt = [x0[j] + sum(K[r, j] * c[r] for r in range(k)) for j in range(n)]
            if ok(pt):
                return {"point": [QQ(v) for v in pt]}
        raise ValueError("no rational witness found")
    # nonlinear: rational points of the equations by Sage's solver, filtered by the side conditions
    import sage.all as S
    sv = [S.SR.var(str(g)) for g in gens]
    res = S.solve([S.SR(str(q)) == 0 for q in eqs], sv, solution_dict=True)
    for sol in res:
        try:
            pt = [QQ(sol[v]) for v in sv]
        except Exception:
            continue
        if ok(pt):
            return {"point": pt}
    raise ValueError("no rational witness found")


# --------------------------------------------------------------------------
# Script sessions: run_script (advisory) and certify (agent certificates)
# --------------------------------------------------------------------------

STDOUT_LIMIT = 20000


class ScriptError(ValueError):
    """A script raised or timed out; carries the stdout it printed before failing."""

    def __init__(self, why, stdout):
        super().__init__(why + (f"\n--- script stdout ---\n{stdout}" if stdout else ""))
        self.stdout = stdout


def _truncate(out):
    if len(out) > STDOUT_LIMIT:
        return out[:STDOUT_LIMIT] + f"\n...[truncated {len(out) - STDOUT_LIMIT} chars]"
    return out


def _run_sage(script, ns, timeout):
    """Run preparsed Sage source in namespace `ns`, bounded by SIGALRM. `sage.all` is imported first, so
    the caller's pre-bound names (e.g. the problem ring `R`) shadow Sage's. Returns the captured stdout;
    raises ScriptError (with that stdout) if the script fails."""
    import contextlib
    import io
    import signal

    from sage.repl.preparse import preparse_file

    prebound = dict(ns)
    exec("from sage.all import *", ns)  # noqa: S102 — untrusted-oracle boundary
    ns.update(prebound)
    code = compile(preparse_file(script), "<veriphy-script>", "exec")
    buf = io.StringIO()

    def _on_alarm(signum, frame):
        raise TimeoutError(f"script exceeded {timeout}s")

    old_handler = signal.signal(signal.SIGALRM, _on_alarm)
    signal.alarm(timeout)
    try:
        with contextlib.redirect_stdout(buf):
            exec(code, ns)  # noqa: S102 — untrusted-oracle boundary
    except Exception as exc:
        raise ScriptError(f"{type(exc).__name__}: {exc}", _truncate(buf.getvalue())) from exc
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
    return _truncate(buf.getvalue())


@method("run_script", advisory=True, script=Str, timeout_s=Int(120))
def do_run_script(script, timeout_s):
    """ADVISORY: run a whole Sage derivation script, as one oracle session.

    The script is preparsed Sage source (loops, defs, random trials, printing
    Lean-ready tables). It communicates structured findings by assigning a
    JSON-safe dict to a top-level variable named `results`; everything it
    prints comes back as `stdout` (truncated beyond 20000 chars). A
    `timeout_s` (default 120) bounds the run via SIGALRM. Guidance only —
    whatever the script discovers must be re-proved in Lean.
    """
    ns = {}
    out = _run_sage(script, ns, timeout_s)
    return {"results": ns.get("results"), "stdout": out, "advisory": True}


Hyp = namedtuple("Hyp", ["name", "poly", "rel"])

FAMILIES = ("identity", "inequality", "witness")


def _bind_problem(problem):
    """Pre-bound script namespace for a serialized Lean problem (see `Veriphy.Kit.Problem.toJson`)."""
    if not isinstance(problem, dict):
        raise ParamError("problem", "must be an object")
    names = problem.get("vars") or []
    ctx = {}
    try:
        _, R = Vars("vars", {"vars": names}, ctx)
    except ParamError as exc:
        raise ParamError("problem", str(exc))

    def hyp(h, i):
        rel = h.get("rel")
        if rel not in RELATIONS:
            raise ParamError("problem", f"constraint {i}: bad relation {rel!r}")
        return Hyp(h.get("name"), _parse_poly("problem", h.get("poly"), ctx), rel)

    hyps = [hyp(h, i) for i, h in enumerate(problem.get("hyps", []))]
    goal_j = problem.get("goal") or {"kind": "false"}
    kind = goal_j.get("kind")
    goal, binders, body = None, [], []
    if kind == "rel":
        goal = hyp(goal_j, "goal")
    elif kind == "exists":
        nb = int(goal_j.get("binders", 0))
        binders = list(R.gens()[:nb])
        body = [hyp(h, f"body {i}") for i, h in enumerate(goal_j.get("body", []))]
    elif kind != "false":
        raise ParamError("problem", f"unknown goal kind {kind!r}")
    atoms = dict(zip(names, problem.get("atoms", [])))
    ns = {"R": R, "hyps": hyps, "goal": goal, "goal_kind": kind, "binders": binders, "body": body,
          "atoms": atoms, "Hyp": Hyp}
    ns.update({str(g): g for g in R.gens()})
    return R, ns


def _qq(v, what):
    try:
        return QQ(v)
    except Exception:
        raise ValueError(f"{what}: {v!r} is not an exact rational")


def _poly(R, v, what):
    try:
        return R(v)
    except Exception:
        raise ValueError(f"{what}: {v!r} is not a polynomial in {R}")


def _validate_certificate(family, cert, R, ns):
    """Normalize a script's `certificate` to its family schema, or raise naming the violation."""
    by_name = {h.name: h for h in ns["hyps"]}

    def hyp_named(nm, allowed):
        if nm not in by_name:
            raise ValueError(f"certificate names unknown hypothesis '{nm}' (known: {sorted(by_name)})")
        if by_name[nm].rel not in allowed:
            raise ValueError(f"hypothesis '{nm}' has relation '{by_name[nm].rel}', not usable by {family}")
        return by_name[nm]

    if family == "identity":
        if ns["goal_kind"] != "rel" or ns["goal"].rel != "eq":
            raise ValueError("identity needs an equality goal")
        cofs = cert.get("cofactors", cert) if isinstance(cert, dict) else None
        if not isinstance(cofs, dict):
            raise ValueError("identity certificate must be {'cofactors': {hyp_name: polynomial}}")
        out = {}
        for nm, c in cofs.items():
            hyp_named(nm, ("eq",))
            out[nm] = _poly(R, c, f"cofactor of {nm}")
        return {"cofactors": [{"name": nm, "poly": c} for nm, c in out.items() if c != 0]}
    if family == "inequality":
        if isinstance(cert, dict) and ("weights" in cert or "squares" in cert):
            weights, squares = cert.get("weights", {}), cert.get("squares", [])
        elif isinstance(cert, dict):
            weights, squares = cert, []
        else:
            raise ValueError("inequality certificate must be {'weights': {...}, 'squares': [(c, q), ...]}")
        ws = []
        for nm, w in weights.items():
            h = hyp_named(nm, ("eq", "le", "lt"))
            if h.rel == "eq":
                ws.append({"name": nm, "poly": _poly(R, w, f"weight of {nm}")})
            else:
                q = _qq(w, f"weight of {nm}")
                if q < 0:
                    raise ValueError(f"weight of inequality hypothesis '{nm}' is negative ({q})")
                ws.append({"name": nm, "poly": R(q)})
        sqs = []
        for i, sq in enumerate(squares):
            if not isinstance(sq, (list, tuple)) or len(sq) != 2:
                raise ValueError(f"square {i} must be a pair (coefficient, polynomial)")
            c = _qq(sq[0], f"square {i} coefficient")
            if c < 0:
                raise ValueError(f"square {i} has a negative coefficient ({c})")
            sqs.append({"coeff": c, "terms": _poly(R, sq[1], f"square {i}")})
        ws = [w for w in ws if w["poly"] != 0]
        sqs = [s for s in sqs if s["coeff"] != 0 and s["terms"] != 0]
        if not ws and not sqs:
            raise ValueError("inequality certificate is empty (every weight is zero)")
        out = {"weights": ws, "squares": sqs}
        if ns["goal_kind"] == "false":
            # refutation: Σ wᵢ pᵢ + Σ cⱼ qⱼ² must be a constant κ with κ > 0, or κ = 0 with a strict weight
            combo = sum((w["poly"] * by_name[w["name"]].poly for w in ws), R.zero())
            combo += sum((s["coeff"] * s["terms"] ** 2 for s in sqs), R.zero())
            if combo.degree() > 0:
                raise ValueError(f"the weighted combination is not constant: {combo}")
            kappa = QQ(combo.constant_coefficient())
            strict = any(by_name[w["name"]].rel == "lt" for w in ws)
            if not (kappa > 0 or (kappa == 0 and strict)):
                raise ValueError(f"the weighted combination gives κ = {kappa}, which is not contradictory")
            out.update({"kappa": kappa, "strict": strict})
        return out
    if family == "witness":
        if ns["goal_kind"] != "exists":
            raise ValueError("witness needs an existential goal")
        pt = cert.get("point") if isinstance(cert, dict) else cert
        if not isinstance(pt, (list, tuple)):
            raise ValueError("witness certificate must be a list of rationals, one per binder")
        if len(pt) != len(ns["binders"]):
            raise ValueError(f"witness has {len(pt)} values for {len(ns['binders'])} binders")
        return {"point": [_qq(v, f"witness value {i}") for i, v in enumerate(pt)]}
    raise ParamError("family", f"must be one of {list(FAMILIES)}")


@method("certify", problem=Json, family=Str, script=Str, timeout_s=Int(120))
def do_certify(problem, family, script, timeout_s):
    """Agent certificate: run `script` with the Lean problem pre-bound (`R`, generators `x0, x1, ...`,
    `hyps` as Hyp(name, poly, rel) with `poly rel 0`, `goal`, `binders`, `body`, `atoms`), read the
    `certificate` it assigns, and validate it against the family schema. UNTRUSTED like every method:
    Lean reconstructs the certificate and a checker family closes the goal."""
    if family not in FAMILIES:
        raise ParamError("family", f"must be one of {list(FAMILIES)}")
    R, ns = _bind_problem(problem)
    out = _run_sage(script, ns, timeout_s)
    if "certificate" not in ns:
        raise ScriptError("the script did not assign `certificate`", out)
    try:
        return _validate_certificate(family, ns["certificate"], R, ns)
    except ValueError as exc:
        raise ScriptError(str(exc), out) from exc


# --------------------------------------------------------------------------
# Advisory symbolic methods
# --------------------------------------------------------------------------


def _symbolic_exprs(strs, names):
    """Parse expression strings in the symbolic ring with the declared variables.

    Each string is an expression, an equation (`lhs == rhs`), or a relation
    (`x > 0`). Parsed with sage_eval, so the full Sage expression language is
    available — acceptable for ADVISORY methods only.
    """
    from sage.all import sage_eval, var

    if not names or not all(isinstance(n, str) and n.isidentifier() for n in names):
        raise ParamError("vars", "must be a non-empty list of identifiers")
    scope = {n: var(n) for n in names}
    return [sage_eval(s, locals=scope) for s in strs]


@method("symbolic_check", advisory=True, raw=True)
def do_symbolic_check(params):
    """ADVISORY: decide whether `lhs == rhs` as a symbolic identity.

    Tries full symbolic simplification first; falls back to numeric sampling.
    Returns {"equal": true|false|null, "method": ..., "advisory": true} plus a
    counterexample when sampling refutes the identity. `null` means undecided:
    simplification did not reach zero but no sampled point refuted it.
    """
    import random

    from sage.all import CDF, assume, forget, var

    names = params.get("vars")
    lhs, rhs = _symbolic_exprs([_get("lhs", params), _get("rhs", params)], names)
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


@method("solve", advisory=True, raw=True)
def do_solve(params):
    """ADVISORY: symbolic solution set of an equation system, as proof guidance.

    Equations are strings (`lhs == rhs`, or an expression meaning `expr == 0`).
    Solutions come back as {var: expression-string} dicts; free parameters keep
    Sage's names (r1, z1, ...). Guidance only — re-prove everything in Lean.
    """
    from sage.all import solve, var

    names = params.get("vars")
    eqs = [
        e if e.is_relational() else (e == 0)
        for e in _symbolic_exprs(_get("equations", params), names)
    ]
    unknowns = [var(v) for v in params.get("solve_for", names)]
    sols = solve(eqs, unknowns, solution_dict=True)
    return {
        "solutions": [{str(v): str(e) for v, e in s.items()} for s in sols],
        "advisory": True,
    }


@method("matrix_check", advisory=True, raw=True)
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
    if not all(isinstance(n, str) and n.isidentifier() for n in names):
        raise ParamError("vars", "must be valid identifiers")
    scope = {n: var(n) for n in names}
    for mname, rows in params.get("matrices", {}).items():
        if not mname.isidentifier():
            raise ParamError("matrices", f"matrix name {mname!r} is not a valid identifier")
        entries = [[sage_eval(str(e), locals=dict(scope)) for e in row] for row in rows]
        scope[mname] = matrix(SR, entries)
    lhs = sage_eval(_get("lhs", params), locals=dict(scope))
    rhs = sage_eval(_get("rhs", params), locals=dict(scope))
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


# --------------------------------------------------------------------------
# Line protocol
# --------------------------------------------------------------------------


def handle(line):
    """One request line -> one response object (never raises)."""
    req_id = None
    try:
        req = json.loads(line)
        req_id = req.get("id")
        name = req.get("method")
        if name not in METHODS:
            return {"id": req_id, "error": f"unknown method '{name}' (known: {sorted(METHODS)})"}
        return {"id": req_id, "result": METHODS[name](req.get("params", {}))}
    except MethodError as exc:
        return {"id": req_id, "error": str(exc)}
    except Exception as exc:  # report, keep serving
        return {"id": req_id, "error": f"{type(exc).__name__}: {exc}"}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        sys.stdout.write(json.dumps(handle(line)) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
