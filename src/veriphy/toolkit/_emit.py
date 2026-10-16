"""Build Lean proof steps from Sage data, as text that re-parses when committed."""

import textwrap
from collections.abc import Sequence

from sage.all import QQ

from veriphy.core import CertificateError, VeriphyError
from veriphy.toolkit._lean import Lean, parenthesize, polynomial, rational, tactic, term
from veriphy.toolkit._problem import Problem

RELATIONS_TEXT = {'eq': '=', 'le': '≤', 'lt': '<'}


def _expect(value: Lean, kind: str, what: str) -> Lean:
    """Return `value`, rejecting Lean text of the wrong syntactic category."""
    if value.kind != kind:
        message = f'{what} must be a Lean {kind}, got a {value.kind}: {value.text}'
        raise VeriphyError(message)
    return value


def _as_term(value: object, problem: Problem) -> Lean:
    """Return a Lean term as is, and render anything else as a polynomial of the problem."""
    if isinstance(value, Lean):
        return _expect(value, 'term', 'an expression')
    return polynomial(value, problem)


def _indent_block(block: Lean) -> str:
    """Return a tactic block indented to sit under a bullet or a `by`."""
    return textwrap.indent(block.text, '  ').lstrip()


def fresh_name(problem: Problem, base: str, taken: Sequence[str] = ()) -> str:
    """Choose a hypothesis name unused in the problem.

    Args:
        problem: The problem whose hypothesis names are taken.
        base: The preferred name.
        taken: Further names to avoid.

    Returns:
        `base`, or `base_1`, `base_2`, ... when `base` is taken.

    Examples:
        >>> from veriphy.toolkit import read_problem
        >>> prob = read_problem({'vars': ['x0'], 'hyps': [{'name': 'h', 'text': 'True'}], 'goal': {'kind': 'false'}})
        >>> fresh_name(prob, 'h'), fresh_name(prob, 'k')
        ('h_1', 'k')
    """
    used = {h.name for h in problem.hyps} | set(taken)
    if base not in used:
        return base
    index = 1
    while f'{base}_{index}' in used:
        index += 1
    return f'{base}_{index}'


def hyp(problem: Problem, name: str) -> Lean:
    """Reference a hypothesis of the problem by name.

    Args:
        problem: The problem.
        name: The hypothesis name.

    Returns:
        The reference, a term.

    Raises:
        CertificateError: If the problem has no hypothesis of that name.

    Examples:
        >>> from veriphy.toolkit import read_problem
        >>> prob = read_problem({'vars': ['x0'], 'hyps': [{'name': 'h1', 'text': 'True'}], 'goal': {'kind': 'false'}})
        >>> str(hyp(prob, 'h1'))
        'h1'
    """
    names = [h.name for h in problem.hyps]
    if name not in names:
        message = f"unknown hypothesis '{name}' (known: {sorted(map(str, names))})"
        raise CertificateError(message)
    return term(name)


def combination(weighted: Sequence[tuple[object, Lean]], problem: Problem) -> Lean:
    """Build the weighted sum `w₁ * p₁ + … + wₖ * pₖ` of proof terms, dropping zero weights.

    Args:
        weighted: Pairs of a weight (a rational or a polynomial of the problem) and a proof term.
        problem: The problem whose atoms the weights are written over.

    Returns:
        The sum, a term.

    Raises:
        CertificateError: If every weight is zero.

    Examples:
        >>> from veriphy.toolkit import read_problem
        >>> prob = read_problem({'vars': ['x0'], 'atoms': ['a'], 'goal': {'kind': 'false'}})
        >>> str(combination([(1, term('h1')), (0, term('h2')), (QQ(-1) / 2, term('h3')), ('x0', term('h4'))], prob))
        'h1 + (-1 / 2) * h3 + (a) * h4'
    """
    pieces = []
    for weight, proof in weighted:
        _expect(proof, 'term', 'a combined proof')
        coefficient = polynomial(weight, problem)
        if coefficient.text == '0':
            continue
        pieces.append(proof.text if coefficient.text == '1' else f'({coefficient}) * {proof}')
    if not pieces:
        message = 'empty combination (every weight is zero)'
        raise CertificateError(message)
    return term(' + '.join(pieces))


def linear_combination(weighted: Sequence[tuple[object, Lean]], problem: Problem) -> Lean:
    """Close an equality or inequality goal by `linear_combination` of weighted proofs.

    Args:
        weighted: Pairs of a weight and a proof term, as for `combination`.
        problem: The problem.

    Returns:
        The tactic.

    Examples:
        >>> from veriphy.toolkit import read_problem
        >>> prob = read_problem({'vars': ['x0'], 'atoms': ['a'], 'goal': {'kind': 'false'}})
        >>> str(linear_combination([('x0 + 3', term('h')), (-2, term("h'"))], prob))
        "linear_combination (a + 3) * h + (-2) * h'"
    """
    return tactic(f'linear_combination {combination(weighted, problem)}')


def sq_nonneg(q: object, problem: Problem) -> Lean:
    """Build the proof term `sq_nonneg (q)`.

    Args:
        q: The expression squared, a Lean term or a polynomial of the problem.
        problem: The problem.

    Returns:
        The term.

    Examples:
        >>> from veriphy.toolkit import read_problem
        >>> prob = read_problem({'vars': ['x0', 'x1'], 'atoms': ['a', 'b'], 'goal': {'kind': 'false'}})
        >>> str(sq_nonneg('x0 - x1', prob))
        'sq_nonneg (a - b)'
    """
    return term(f'sq_nonneg ({_as_term(q, problem)})')


def mul_nonneg(left: Lean, right: Lean) -> Lean:
    """Build the proof term `mul_nonneg left right` from two nonnegativity proofs.

    Args:
        left: A proof of `0 ≤ a`.
        right: A proof of `0 ≤ b`.

    Returns:
        A proof of `0 ≤ a * b`.

    Examples:
        >>> str(mul_nonneg(term('ha'), term('sq_nonneg b')))
        'mul_nonneg ha (sq_nonneg b)'
    """
    return term(f'mul_nonneg {parenthesize(left.text)} {parenthesize(right.text)}')


def mul_pos(left: Lean, right: Lean) -> Lean:
    """Build the proof term `mul_pos left right` from two positivity proofs.

    Args:
        left: A proof of `0 < a`.
        right: A proof of `0 < b`.

    Returns:
        A proof of `0 < a * b`.

    Examples:
        >>> str(mul_pos(term('ha'), term('hb')))
        'mul_pos ha hb'
    """
    return term(f'mul_pos {parenthesize(left.text)} {parenthesize(right.text)}')


def _with_list(name: str, items: Sequence[object], suffix: str = '') -> Lean:
    """Return `name [i₁, …, iₙ]` (without the brackets when empty), followed by `suffix`."""
    rendered = ', '.join(str(i) for i in items)
    return tactic(f'{name} [{rendered}]{suffix}' if rendered else f'{name}{suffix}')


def nlinarith(hints: Sequence[Lean] = ()) -> Lean:
    """Call `nlinarith` with hint terms (products and squares that Sage found).

    Args:
        hints: Proof terms added to `nlinarith`'s atom set.

    Returns:
        The tactic.

    Examples:
        >>> str(nlinarith([term('sq_nonneg (a - b)'), term('mul_pos ha hb')]))
        'nlinarith [sq_nonneg (a - b), mul_pos ha hb]'
    """
    return _with_list('nlinarith', [_expect(h, 'term', 'an nlinarith hint') for h in hints])


def positivity() -> Lean:
    """Call `positivity`.

    Returns:
        The tactic.

    Examples:
        >>> str(positivity())
        'positivity'
    """
    return tactic('positivity')


def field_simp(lemmas: Sequence[str] = ()) -> Lean:
    """Call `field_simp`, optionally with extra simp lemmas (such as nonzero-denominator facts).

    Args:
        lemmas: Lemma or hypothesis names.

    Returns:
        The tactic.

    Examples:
        >>> str(field_simp(['hx']))
        'field_simp [hx]'
    """
    return _with_list('field_simp', lemmas)


def norm_num(lemmas: Sequence[str] = (), at: str | None = None) -> Lean:
    """Call `norm_num`, optionally with extra simp lemmas and at a hypothesis.

    Args:
        lemmas: Lemma or hypothesis names.
        at: A hypothesis to normalize instead of the goal.

    Returns:
        The tactic.

    Examples:
        >>> str(norm_num()), str(norm_num(at='hk'))
        ('norm_num', 'norm_num at hk')
    """
    return _with_list('norm_num', lemmas, f' at {at}' if at else '')


def decide() -> Lean:
    """Call `decide`, for decidable goals over finite domains.

    Returns:
        The tactic.

    Examples:
        >>> str(decide())
        'decide'
    """
    return tactic('decide')


def rewrite_by(lhs: object, rhs: object, justification: Lean, problem: Problem) -> Lean:
    """Rewrite `lhs` into `rhs`, justified by a tactic: `rw [show lhs = rhs by tac]`.

    Args:
        lhs: The expression to rewrite, a Lean term or a polynomial of the problem.
        rhs: Its replacement.
        justification: A tactic proving `lhs = rhs`, such as `ring1`.
        problem: The problem.

    Returns:
        The tactic.

    Examples:
        >>> from veriphy.toolkit import read_problem
        >>> prob = read_problem({'vars': ['x0'], 'atoms': ['x'], 'goal': {'kind': 'false'}})
        >>> str(rewrite_by('x0^2 - 1', term('(x - 1) * (x + 1)'), tactic('ring1'), prob))
        'rw [show x ^ 2 - 1 = (x - 1) * (x + 1) by ring1]'
    """
    proof = _expect(justification, 'tactic', 'a rewrite justification')
    return tactic(f'rw [show {_as_term(lhs, problem)} = {_as_term(rhs, problem)} by {proof}]')


def calc_chain(start: object, steps: Sequence[tuple[str, object, Lean]], problem: Problem) -> Lean:
    """Build a `calc` chain from `start` through each step's expression, every step with its own tactic.

    Args:
        start: The first expression, a Lean term or a polynomial of the problem.
        steps: Triples of a relation (`=`, `≤`, `<`, or `eq`, `le`, `lt`), the next expression and the tactic proving
            the step.
        problem: The problem.

    Returns:
        The tactic.

    Raises:
        VeriphyError: If there are no steps.

    Examples:
        >>> from veriphy.toolkit import read_problem
        >>> prob = read_problem({'vars': ['x0'], 'atoms': ['x'], 'goal': {'kind': 'false'}})
        >>> print(calc_chain('(x0 + 1)^2', [('=', 'x0^2 + 2*x0 + 1', tactic('ring'))], prob))
        calc x ^ 2 + 2 * x + 1
            _ = x ^ 2 + 2 * x + 1 := by ring
    """
    if not steps:
        message = 'a calc chain needs at least one step'
        raise VeriphyError(message)
    lines = [f'calc {_as_term(start, problem)}']
    for relation, expression, proof in steps:
        symbol = RELATIONS_TEXT.get(relation, relation)
        tac = _expect(proof, 'tactic', 'a calc step proof')
        lines.append(f'    _ {symbol} {_as_term(expression, problem)} := by {tac}')
    return tactic('\n'.join(lines))


def by_cases(name: str, proposition: Lean, positive: Lean, negative: Lean) -> Lean:
    """Split on a proposition, with one tactic block per branch.

    Args:
        name: The hypothesis name in each branch (use `fresh_name`).
        proposition: The proposition split on, a term.
        positive: The block for the branch where it holds.
        negative: The block for the branch where it fails.

    Returns:
        The tactic.

    Examples:
        >>> print(by_cases('hx', term('x ≤ 0'), tactic('nlinarith'), tactic('positivity')))
        by_cases hx : x ≤ 0
        · nlinarith
        · positivity
    """
    _expect(proposition, 'term', 'a split proposition')
    blocks = [_expect(b, 'tactic', 'a branch') for b in (positive, negative)]
    return tactic(f'by_cases {name} : {proposition}\n' + '\n'.join(f'· {_indent_block(b)}' for b in blocks))


def rcases(target: Lean, names: Sequence[str], branches: Sequence[Lean]) -> Lean:
    """Split a disjunction proof into branches, naming the hypothesis of each.

    Args:
        target: A proof of a disjunction `p₁ ∨ … ∨ pₙ`.
        names: One hypothesis name per disjunct.
        branches: One tactic block per disjunct.

    Returns:
        The tactic.

    Raises:
        VeriphyError: If the numbers of names and branches differ.

    Examples:
        >>> print(rcases(term('le_or_lt x 0'), ['hx', 'hx'], [tactic('nlinarith'), tactic('positivity')]))
        rcases le_or_lt x 0 with hx | hx
        · nlinarith
        · positivity
    """
    if len(names) != len(branches):
        message = f'rcases has {len(names)} names for {len(branches)} branches'
        raise VeriphyError(message)
    pattern = ' | '.join(names)
    blocks = '\n'.join(f'· {_indent_block(_expect(b, "tactic", "a branch"))}' for b in branches)
    return tactic(f'rcases {_expect(target, "term", "a disjunction proof")} with {pattern}\n{blocks}')


def witness(values: Sequence[object], side: Lean) -> Lean:
    """Close an existential goal with exact rational values and a tactic for the side conditions.

    Args:
        values: One rational per binder.
        side: The tactic proving the body at those values, such as `norm_num`.

    Returns:
        The tactic.

    Examples:
        >>> str(witness([1, QQ(-1) / 2], tactic('norm_num')))
        'exact ⟨1, -(1 / 2), by norm_num⟩'
    """
    rendered = ', '.join(str(rational(v)) for v in values)
    return tactic(f'exact ⟨{rendered}, by {_expect(side, "tactic", "a side-goal tactic")}⟩')


def negate_goal(name: str) -> Lean:
    """Turn a `≤`/`<` goal into `False` with its negation as hypothesis `name`.

    Args:
        name: The name of the negated goal (use `fresh_name`).

    Returns:
        The tactic block.

    Examples:
        >>> print(negate_goal('hneg'))
        by_contra hneg
        push Not at hneg
    """
    return steps(tactic(f'by_contra {name}'), tactic(f'push Not at {name}'))


def refute(kappa: object, *, strict: bool, weighted: Sequence[tuple[object, Lean]], problem: Problem) -> Lean:
    """Close `False` from a combination of hypotheses that reduces to the contradictory constant `κ`.

    The combination proves `κ ≤ 0` (or `κ < 0` when `strict`), which `norm_num` refutes.

    Args:
        kappa: The constant the combination reduces to, positive (or zero when `strict`).
        strict: Whether the combination uses a strict hypothesis.
        weighted: Pairs of a weight and a hypothesis proof, as for `combination`.
        problem: The problem, which must name its carrier type.

    Returns:
        The tactic block.

    Raises:
        VeriphyError: If the problem does not name its carrier type.

    Examples:
        >>> from veriphy.toolkit import read_problem
        >>> prob = read_problem({'vars': ['x0'], 'carrier': 'ℚ', 'goal': {'kind': 'false'}})
        >>> print(refute(2, strict=False, weighted=[(1, term('h1')), (-1, term('h2'))], problem=prob))
        have hκ : (2 : ℚ) ≤ 0 := by linear_combination h1 + (-1) * h2
        norm_num at hκ
    """
    if not problem.carrier:
        message = 'refute needs the problem carrier type (such as ℚ) to state the constant'
        raise VeriphyError(message)
    name = fresh_name(problem, 'hκ')
    relation = '<' if strict else '≤'
    statement = f'have {name} : ({rational(QQ(kappa))} : {problem.carrier}) {relation} 0'
    return steps(
        tactic(f'{statement} := by linear_combination {combination(weighted, problem)}'),
        norm_num(at=name),
    )


def sum_by_induction(variable: str, index_set: str = 'range', lower: int = 0) -> Lean:
    """Prove `∑ k ∈ s n, f k = F n` by induction on `n`, each case by `push_cast` and `ring1`.

    The index set `s n` is `Finset.range n`, `Finset.Icc lower n` or `Finset.Ico lower n`, with `lower` 0 or 1 (a
    sum from elsewhere is first rewritten to start there, for example with `Finset.sum_Ico_eq_sum_range`).

    Args:
        variable: The name of the natural-number variable `n`.
        index_set: `range`, `Icc` or `Ico`.
        lower: The lower bound of an `Icc` or `Ico` sum, 0 or 1.

    Returns:
        The tactic block.

    Raises:
        VeriphyError: If the index set or lower bound is not supported.

    Examples:
        >>> print(sum_by_induction('n'))
        induction n with
        | zero => rw [Finset.sum_range_zero]; (try push_cast); ring1
        | succ n ih => rw [Finset.sum_range_succ, ih]; (try push_cast); ring1
        >>> print(sum_by_induction('n', 'Icc', 1))
        induction n with
        | zero => simp
        | succ n ih => rw [Finset.sum_Icc_succ_top (by omega), ih]; (try push_cast); ring1
    """
    if index_set == 'range':
        return tactic(
            f'induction {variable} with\n'
            '| zero => rw [Finset.sum_range_zero]; (try push_cast); ring1\n'
            f'| succ {variable} ih => rw [Finset.sum_range_succ, ih]; (try push_cast); ring1',
        )
    if index_set not in ('Icc', 'Ico') or lower not in (0, 1):
        message = (
            f'sum_by_induction handles range, and Icc or Ico from 0 or 1, not {index_set} from {lower}; '
            'rewrite the sum with Finset.sum_Ico_eq_sum_range first'
        )
        raise VeriphyError(message)
    if index_set == 'Icc' or lower == 0:
        return tactic(
            f'induction {variable} with\n'
            '| zero => simp\n'
            f'| succ {variable} ih => rw [Finset.sum_{index_set}_succ_top (by omega), ih]; (try push_cast); ring1',
        )
    return tactic(
        f'induction {variable} with\n'
        '| zero => simp\n'
        f'| succ {variable} ih =>\n'
        f'  rcases Nat.eq_zero_or_pos {variable} with h | h\n'
        '  · subst h; simp\n'
        '  · rw [Finset.sum_Ico_succ_top h, ih]; (try push_cast); ring1',
    )


def steps(*blocks: Lean) -> Lean:
    """Sequence tactic blocks, one after another.

    Args:
        *blocks: The tactics, in order.

    Returns:
        The combined tactic block.

    Raises:
        VeriphyError: If there are no blocks.

    Examples:
        >>> print(steps(tactic('intro x'), tactic('positivity')))
        intro x
        positivity
    """
    if not blocks:
        message = 'steps needs at least one tactic'
        raise VeriphyError(message)
    return tactic('\n'.join(_expect(b, 'tactic', 'a step').text for b in blocks))


def first_of(*alternatives: Lean) -> Lean:
    r"""Return a tactic trying each alternative in order until one closes the goal.

    Veriphy prints the alternative that closed it as the replacement.

    Args:
        *alternatives: The tactics, tried in order.

    Returns:
        The tactic `first | … | …`.

    Raises:
        CertificateError: If no alternative is given.

    Examples:
        >>> print(first_of(tactic('ring1'), tactic('rw [h]\nring')))
        first
        | ring1
        | rw [h]
          ring
    """
    if not alternatives:
        message = 'first_of needs at least one alternative'
        raise CertificateError(message)
    blocks = [_expect(a, 'tactic', 'every alternative of first_of').text for a in alternatives]
    return tactic('first\n' + '\n'.join('| ' + b.replace('\n', '\n  ') for b in blocks))
