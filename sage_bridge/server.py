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


METHODS = {
    "ping": lambda params: {"ok": True, "sage": version()},
    "factor": do_factor,
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
