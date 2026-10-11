"""Daemon tests. Run with `sage -python -m unittest sage_bridge/test_server.py` from the repo root."""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import server  # noqa: E402
from sage.all import QQ, PolynomialRing, RealField  # noqa: E402


def call(method, **params):
    """Send one request through the line protocol; return the response object."""
    return server.handle(json.dumps({"id": 7, "method": method, "params": params}))


def ok(method, **params):
    resp = call(method, **params)
    if "error" in resp:
        raise AssertionError(resp["error"])
    return resp["result"]


def err(method, **params):
    resp = call(method, **params)
    if "error" not in resp:
        raise AssertionError(f"expected an error, got {resp['result']}")
    return resp["error"]


class Framework(unittest.TestCase):
    def test_encode_exact(self):
        R = PolynomialRing(QQ, 2, ["x0", "x1"])
        x0, x1 = R.gens()
        self.assertEqual(server.encode(QQ(1) / 3), "1/3")
        self.assertEqual(server.encode({"m": [QQ(-3) / 2, 5]}), {"m": ["-3/2", 5]})
        self.assertEqual(server.encode(2 * x0 ** 2 * x1 - 1),
                         [{"coeff": "-1", "exps": [0, 0]}, {"coeff": "2", "exps": [2, 1]}])

    def test_encode_rejects_floats_in_certificates(self):
        with self.assertRaises(TypeError):
            server.encode(0.5)
        with self.assertRaises(TypeError):
            server.encode(RealField(53)(0.5))
        self.assertEqual(server.encode(0.5, advisory=True), 0.5)
        self.assertEqual(server.encode(RealField(53)(0.5), advisory=True), "0.500000000000000")

    def test_unknown_method(self):
        resp = call("nosuch")
        self.assertEqual(resp["id"], 7)
        self.assertIn("nosuch", resp["error"])

    def test_invalid_vars_names_parameter_and_keeps_serving(self):
        e = err("factor", poly="x0", vars=["x0", "1y"])
        self.assertTrue(e.startswith("factor: "), e)
        self.assertIn("'vars'", e)
        self.assertEqual(ok("factor", poly="x0^2 - 1", vars=["x0"])["unit"], "1")

    def test_missing_and_foreign_polynomial(self):
        self.assertIn("'poly'", err("factor", vars=["x0"]))
        self.assertIn("'poly'", err("factor", poly="x0 + y", vars=["x0"]))

    def test_bad_relation(self):
        self.assertIn("'rels'", err("farkas", polys=["x0"], rels=["ne"], vars=["x0"]))

    def test_ping(self):
        resp = server.handle('{"id":1,"method":"ping"}')
        self.assertEqual(resp["id"], 1)
        self.assertTrue(resp["result"]["ok"])
        self.assertIn("sage", resp["result"])


class ExactLP(unittest.TestCase):
    def test_no_variables(self):
        self.assertEqual(server.exact_lp(0), [])
        self.assertIsNone(server.exact_lp(0, les=[([], 1)]))  # 1 <= 0

    def test_no_constraints(self):
        self.assertEqual(server.exact_lp(3, nonneg=True), [0, 0, 0])

    def test_constant_rows_decided_directly(self):
        self.assertEqual(server.exact_lp(2, eqs=[([0, 0], 0)]), [0, 0])
        self.assertIsNone(server.exact_lp(2, eqs=[([0, 0], 1)]))

    def test_infeasible(self):
        # t <= 0 and t >= 1
        self.assertIsNone(server.exact_lp(1, les=[([1], 0), ([-1], 1)]))

    def test_fractional_solution(self):
        # 3 t = 1
        sol = server.exact_lp(1, eqs=[([3], -1)])
        self.assertEqual(sol, [QQ(1) / 3])
        self.assertEqual(server.encode(sol), ["1/3"])


class CertificateMethods(unittest.TestCase):
    """Shapes unchanged, on the inputs VeriphyTest.lean sends."""

    def test_factor(self):
        r = ok("factor", poly="(3 * x0^2 * x1) - (3 * x1^3)", vars=["x0", "x1"])
        self.assertEqual(r["unit"], "3")
        self.assertEqual({tuple(sorted(f)) for f in r["factors"]}, {("mult", "terms")})
        self.assertEqual(len(r["factors"]), 3)

    def test_sos_factor_route(self):
        r = ok("sos", poly="x0^4 - 2*x0^3 + 2*x0^2 - 2*x0 + 1", vars=["x0"])
        self.assertTrue(r["squares"])
        self.assertEqual(set(r["squares"][0]), {"coeff", "terms"})

    def test_sos_single_variable_quadratic(self):
        r = ok("sos", poly="x0^2 + x0 + 1", vars=["x0"])
        self.assertEqual(len(r["squares"]), 2)

    def test_sos_hints(self):
        r = ok("sos", poly="x0^4 + 2*x0^2*x1^2 + x1^4 - 2*x0^2 - 2*x1^2 + 1 + (x0 - x1)^2",
               vars=["x0", "x1"], hints=["x0^2 + x1^2 - 1", "x0 - x1"])
        self.assertEqual(len(r["squares"]), 2)
        self.assertIn("no nonnegative combination",
                      err("sos", poly="-1", vars=["x0"], hints=["x0"]))

    def test_roots(self):
        r = ok("roots", poly="2*x0^3 - 3*x0^2 - 3*x0 + 2", var="x0")
        self.assertEqual(sorted(r["roots"]), sorted(["-1", "1/2", "2"]))

    def test_lincomb(self):
        r = ok("lincomb", target="(x0^2 + x1^2) - (5)", hyps=["(x0 + x1) - (3)", "(x0*x1) - (2)"],
               vars=["x0", "x1"])
        self.assertEqual(len(r["cofactors"]), 2)
        self.assertIn("'hyps'", err("lincomb", target="x0", hyps=[], vars=["x0"]))

    def test_sum(self):
        r = ok("sum", summand="k^2")
        self.assertEqual(r["var"], "n")
        self.assertEqual({t["coeff"] for t in r["closed_form"]}, {"1/3", "-1/2", "1/6"})

    def test_farkas(self):
        r = ok("farkas", polys=["(x0 + x1) - (1)", "(x0 - x1) - (3)", "(0) - (x1)"],
               rels=["le", "eq", "le"], vars=["x0", "x1"])
        self.assertEqual(set(r), {"multipliers", "kappa", "strict"})
        self.assertTrue(QQ(r["kappa"]) > 0)

    def test_farkas_strict(self):
        r = ok("farkas", polys=["x0 - x1", "x1 - x0"], rels=["lt", "le"], vars=["x0", "x1"])
        self.assertTrue(r["strict"])
        self.assertEqual(r["kappa"], "0")

    def test_farkas_consistent(self):
        e = err("farkas", polys=["x0 - 1"], rels=["le"], vars=["x0"])
        self.assertTrue(e.startswith("farkas: "), e)
        self.assertIn("no Farkas certificate", e)

    def test_farkas_only_equalities(self):
        # empty-LP regression: no inequality rows besides kappa
        e = err("farkas", polys=["x0 - x1", "x1 - x2"], rels=["eq", "eq"], vars=["x0", "x1", "x2"])
        self.assertIn("no Farkas certificate", e)
        r = ok("farkas", polys=["x0 - 1", "x0 - 2"], rels=["eq", "eq"], vars=["x0"])
        self.assertTrue(QQ(r["kappa"]) > 0)

    def test_exists(self):
        r = ok("exists", vars=["x0", "x1"], eqs=["2*x0 + x1 - 3*x0", "x0 + 2*x1 - 3*x1"], nes=["x0"])
        self.assertEqual(len(r["point"]), 2)
        r = ok("exists", vars=["x0", "x1"], eqs=["x0 + x1 - 1"], lts=["0 - x0", "x0 - x1"])
        x, y = map(QQ, r["point"])
        self.assertTrue(x + y == 1 and 0 < x < y)

    def test_exists_no_inequalities(self):
        r = ok("exists", vars=["x0", "x1"], eqs=["x0 - x1"])
        self.assertEqual(r["point"][0], r["point"][1])


class ScriptMethods(unittest.TestCase):
    def test_run_script(self):
        r = ok("run_script", script="print('hi')\nresults = {'a': 1/3, 'b': [1, 2]}")
        self.assertEqual(set(r), {"results", "stdout", "advisory"})
        self.assertEqual(r["results"], {"a": "1/3", "b": ["1", "2"]})  # Sage Integers, exact
        self.assertEqual(r["stdout"], "hi\n")

    def test_run_script_error_carries_stdout(self):
        e = err("run_script", script="print('before')\n1/0")
        self.assertIn("ZeroDivisionError", e)
        self.assertIn("before", e)


PROBLEM_INEQ = {
    "vars": ["x0", "x1"], "atoms": ["x", "y"],
    "hyps": [{"name": "h1", "poly": "(x0 + x1) - (1)", "rel": "le"},
             {"name": "h2", "poly": "(x0 - x1) - (3)", "rel": "eq"},
             {"name": "h3", "poly": "(0) - (x1)", "rel": "le"}],
    "goal": {"kind": "false"},
}

PROBLEM_EXISTS = {
    "vars": ["x0", "x1"], "atoms": ["v₁", "v₂"], "hyps": [],
    "goal": {"kind": "exists", "binders": 2,
             "body": [{"poly": "x0 + x1 - 1", "rel": "eq"}, {"poly": "0 - x0", "rel": "lt"}]},
}


class Certify(unittest.TestCase):
    def test_inequality_well_formed(self):
        script = "assert [h.name for h in hyps] == ['h1', 'h2', 'h3']\n" \
                 "assert hyps[0].poly == x0 + x1 - 1 and hyps[0].rel == 'le'\n" \
                 "certificate = {'weights': {'h1': 1, 'h2': -1, 'h3': 2}}"
        r = ok("certify", problem=PROBLEM_INEQ, family="inequality", script=script)
        self.assertEqual([w["name"] for w in r["weights"]], ["h1", "h2", "h3"])
        self.assertEqual(r["weights"][1]["poly"], [{"coeff": "-1", "exps": [0, 0]}])
        self.assertEqual(r["squares"], [])

    def test_inequality_refutation_kappa(self):
        r = ok("certify", problem=PROBLEM_INEQ, family="inequality",
               script="certificate = {'h1': 1, 'h2': -1, 'h3': 2}")
        self.assertEqual((r["kappa"], r["strict"]), ("2", False))
        e = err("certify", problem=PROBLEM_INEQ, family="inequality", script="certificate = {'h1': 1}")
        self.assertIn("not constant", e)

    def test_inequality_shorthand_and_squares(self):
        prob = {"vars": ["x0", "x1"], "atoms": ["a", "b"], "hyps": [],
                "goal": {"kind": "rel", "poly": "x0*x1 - (x0^2 + x1^2)/2", "rel": "le"}}
        r = ok("certify", problem=prob, family="inequality",
               script="certificate = {'squares': [(1/2, x0 - x1)]}")
        self.assertEqual(r["squares"][0]["coeff"], "1/2")

    def test_negative_weight(self):
        e = err("certify", problem=PROBLEM_INEQ, family="inequality",
                script="certificate = {'h1': -1}")
        self.assertIn("negative", e)

    def test_missing_certificate(self):
        e = err("certify", problem=PROBLEM_INEQ, family="inequality", script="print('thinking')")
        self.assertIn("did not assign `certificate`", e)
        self.assertIn("thinking", e)

    def test_unknown_hypothesis(self):
        e = err("certify", problem=PROBLEM_INEQ, family="inequality", script="certificate = {'h9': 1}")
        self.assertIn("'h9'", e)

    def test_witness(self):
        r = ok("certify", problem=PROBLEM_EXISTS, family="witness",
               script="certificate = [QQ(1)/3, QQ(2)/3]")
        self.assertEqual(r["point"], ["1/3", "2/3"])

    def test_witness_arity(self):
        e = err("certify", problem=PROBLEM_EXISTS, family="witness", script="certificate = [1]")
        self.assertIn("1 values for 2 binders", e)

    def test_identity(self):
        prob = {"vars": ["x0", "x1"], "atoms": ["a", "b"],
                "hyps": [{"name": "h", "poly": "(x0 + x1) - (3)", "rel": "eq"},
                         {"name": "h'", "poly": "(x0*x1) - (2)", "rel": "eq"}],
                "goal": {"kind": "rel", "poly": "(x0^2 + x1^2) - (5)", "rel": "eq"}}
        script = "g = goal.poly\ncs = g.lift(R.ideal([h.poly for h in hyps]))\n" \
                 "certificate = {'cofactors': {h.name: c for h, c in zip(hyps, cs)}}"
        r = ok("certify", problem=prob, family="identity", script=script)
        self.assertEqual([c["name"] for c in r["cofactors"]], ["h", "h'"])

    def test_script_raises(self):
        e = err("certify", problem=PROBLEM_INEQ, family="inequality",
                script="print('step 1')\n1/0")
        self.assertIn("ZeroDivisionError", e)
        self.assertIn("step 1", e)

    def test_bad_family(self):
        self.assertIn("'family'", err("certify", problem=PROBLEM_INEQ, family="sum", script=""))


if __name__ == "__main__":
    unittest.main()
