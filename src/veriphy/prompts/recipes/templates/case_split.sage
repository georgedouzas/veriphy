# name: case_split
# technique: case split
# goal: a statement that is easy on each side of a sign or comparison condition
# description: Split on a condition Sage suggests; each branch gets its own tactic.
condition = term('0 ≤ x')  # EDIT: the split, in the goal's terms (Sage can locate sign changes with real_roots)
name = fresh_name(problem, 'hx')
on_true = tactic(f'exact mul_nonneg {name} {name}')  # EDIT: the branch where the condition holds
on_false = nlinarith()  # EDIT: the branch where it fails
proof = by_cases(name, condition, on_true, on_false)
