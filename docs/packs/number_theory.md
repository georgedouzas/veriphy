# The `number-theory` pack

The `number-theory` pack checks number-theoretic claims with PARI/GP, the library Sage ships: a factorization into
primes, with each prime's primality proven, and a number field's class number, certified without assuming the
generalized Riemann hypothesis. It is a subfield of [`math`](math.md), nested in its pack, and runs under Sage through
the math pack's `sage` tool.

```yaml
# veriphy.yaml
version: 1
packs: [number-theory]
```

## Checks

```console
$ veriphy layers step check-factorization 147573952589676412927 "193707721 * 761838257287" --claim mersenne-67
check-factorization 147573952589676412927: accepted
  level: oracle-test (oracle)
  record: .veriphy/runs/check-factorization/….json
$ veriphy layers step check-factorization 147573952589676412927 147573952589676412927
check-factorization 147573952589676412927: refused
  why: 147573952589676412927 is not prime
  record: .veriphy/runs/check-factorization/….json
$ veriphy layers step check-class-number "x^2 + 23" 1
check-class-number x^2 + 23: refused
  why: the class number is 3, not 1
  record: .veriphy/runs/check-class-number/….json
```

A factorization is a product of primes and powers, `2^3 * 3 * 5`. Primality is PARI's `isprime`, a proof by APR-CL or
ECPP, not a probable-prime test. A class number comes from `bnfinit`, which assumes GRH, then `bnfcertify`, which
removes the assumption; a class group PARI cannot certify leaves the claim `undecided`.

## Steps and levels

| Step | Kind | Does | Grants |
|---|---|---|---|
| `check-factorization <number> <claimed>` | check | checks a factorization, proving each factor prime | `oracle-test` |
| `check-class-number <polynomial> <claimed>` | check | checks a class number, certified | `oracle-test` |

Both grant the math pack's `oracle-test`: PARI is part of Sage, an oracle. A proof of the claim in Lean, with the
math pack's `check`, grants more.
