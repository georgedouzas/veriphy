# Primality

## When to use

- The goal is `Nat.Prime p` for an explicit numeral `p` too large for `norm_num`'s primality extension (tens of
  digits).
- Sage factors `p - 1` recursively into a Pratt certificate: for each prime `q` in the tree, a witness `a` of order
  `q - 1` and the factorization of `q - 1`. `VeriphyCheck.prime_of_pratt` checks it by `decide +kernel` (the kernel's
  big-number arithmetic, no `native_decide`).

## Template

Copy it to the project's `.veriphy/certificates/primality.sage` (or a more specific name), adapt the lines marked `EDIT`,
keep the header, and run it with `sage_run file "<name>.sage"`.

```sage
# name: primality
# technique: Pratt certificate, checked by the kernel
# goal: Nat.Prime p for an explicit p, beyond norm_num's primality extension
# description: Sage factors p - 1 recursively; VeriphyCheck.prime_of_pratt checks the certificate by decide +kernel.
import re
found = re.search(r'Nat\.Prime (\d+)', goal.text if goal is not None else '')
assert found, 'the goal must be Nat.Prime p for an explicit numeral p'
p = Integer(found.group(1))
assert p.is_prime(), f'{p} is not prime: {p.factor()}'
proof = tactic('exact ' + str(prime_certificate(p)))
```

## Worked examples

```lean
example : Nat.Prime 1000000000000000000000000000000000012397 := by
  sage_run file "primality.sage"
-- replacement: exact VeriphyCheck.prime_of_pratt (cert := [(3, 2, [(2, 1)]), …]) (by decide +kernel)
```

## Failure modes

- **"the goal must be Nat.Prime p for an explicit numeral p":** the statement is symbolic in `p`; this recipe
  certifies one number.
- **"p is not prime":** the message shows the factorization.
- **Slow checks:** hundreds of digits make the certificate tree deep; the kernel's arithmetic is exact but grows with
  the size.
