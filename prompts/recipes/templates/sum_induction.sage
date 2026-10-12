# name: sum_induction
# technique: closed-form sum by induction
# goal: ∑ k ∈ Finset.range n, f k = F n, with the closed form F already stated
# description: Induction on n; both cases close by push_cast and ring1. Sage only finds F (see the recipe).
import re
found = re.search(r'Finset\.range (\w+)', goal.text if goal is not None else '')
assert found, 'the goal must be a sum over Finset.range n'
proof = sum_by_induction(found.group(1))
