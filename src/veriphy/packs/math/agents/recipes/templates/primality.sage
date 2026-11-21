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
