# name: round_trip
# technique: symbolic rendering round trip
# goal: True, from a hypothesis `h : E = 0`
# description: renders the symbolic form of `h` back to Lean and proves it equal to `E` by `linear_combination h`
h = hyps[0]
proof = steps(tactic(f'have _r : {symbolic(h.expr, problem)} = 0 := by linear_combination {h.name}'), tactic('trivial'))
