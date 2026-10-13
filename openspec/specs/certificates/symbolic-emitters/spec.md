# certificates/symbolic-emitters Specification

## Purpose
Lets scripts write Lean proofs over the full symbolic structure Sage computes with: rational functions, transcendental expressions and matrices. Scripts get denominator- and domain-aware tactic calls, so Lean can check the result.

## Requirements

### Requirement: Render symbolic expressions
The toolkit SHALL render Sage symbolic-ring expressions, rational functions and matrices as Lean terms over the problem's atoms, through an explicit function table: `sqrt`, `exp`, `log`, `sin`, `cos`, `tan` → their `Real` versions (`Complex` for ℂ); `pi` → `Real.pi`, `I` → `Complex.I`; `abs` → `|·|`; matrices → `!![…]` literals; and every entry of the project's translation tables. An unmapped function SHALL be rejected with an error naming it and pointing at the project translation tables.

#### Scenario: Absolute value of a real
- **WHEN** a script renders `abs(x0 - 1)` with `x0` a real atom
- **THEN** the text is `|x - 1|`, never `Int.natAbs`

#### Scenario: Complex exponential
- **WHEN** a script renders `exp(x0)` with `x0` a complex atom
- **THEN** the text is `Complex.exp z`

#### Scenario: Unmapped function
- **WHEN** a script renders `gamma(x0)` and no project entry maps `gamma`
- **THEN** the toolkit raises an error naming `gamma` and the `.veriphy/translations/` directory

#### Scenario: Project entry
- **WHEN** the project has an entry mapping Sage `cosh` to `Real.cosh` and a script renders `cosh(x0)`
- **THEN** the text is `Real.cosh x`

### Requirement: Render special and integer functions
The function table SHALL also render `cosh`, `sinh`, `tanh`, `arctan`, `arcsin`, `arccos` as their `Real` versions, `logb(b, x)` (the script's form of `log(x)/log(b)`) as `Real.logb b x`, a power with a non-integer exponent as `x ^ (y : ℝ)`, and `factorial`, `binomial`, `gcd`, `floor`, `ceil` as `Nat.factorial`, `Nat.choose`, `Nat.gcd` or `Int.gcd`, `Int.floor` and `Int.ceil`.

#### Scenario: Real power and binomial
- **WHEN** a script renders `x0^(1/3) + binomial(n, 2)` with `x0` a real atom and `n` a natural atom
- **THEN** the power is rendered in `Real.rpow` notation `x ^ (… : ℝ)` and the binomial as `Nat.choose n 2`

### Requirement: Domain-aware tactic builders
The toolkit SHALL build `field_simp` and `positivity`-based steps that pass the problem's discharged domain conditions as facts. It SHALL refuse to build a step whose required conditions are undischarged, naming them, unless the caller supplies a proof step for each.

#### Scenario: Clearing denominators
- **WHEN** a script clears denominators in a goal with `1 / y`, and `hy : y ≠ 0` discharges the condition
- **THEN** the step is `field_simp [hy]`, or an equivalent that passes `hy`

#### Scenario: Missing condition
- **WHEN** the required condition `0 < x` for `Real.log x` is undischarged
- **THEN** the builder fails with an error naming `0 < x`, unless a proof step for it is supplied

### Requirement: Rewrite chains with named lemmas
The toolkit SHALL build rewrite and `calc` steps justified by named mathlib lemmas, passing the lemma's side conditions from the domain conditions. It SHALL provide one rewrite table, made of core entries for exponentials, logarithms, powers, square roots and trigonometric and hyperbolic identities (such as `Real.exp_add`, `Real.log_mul`, `Real.cosh_sq`) and the project's entries, each with its functions and side conditions. Scripts and recipes SHALL select rewrites from it.

#### Scenario: Exponential identity
- **WHEN** a script proves `Real.exp a * Real.exp b = Real.exp (a + b)` with a rewrite by `Real.exp_add`
- **THEN** the emitted step is `rw [← Real.exp_add]` (or equivalent), and it closes the goal

#### Scenario: Side condition from the table
- **WHEN** a script selects `Real.log_mul` for `Real.log (x * y)` and the context has `hx : x ≠ 0` and `hy : y ≠ 0`
- **THEN** the emitted step passes `hx` and `hy`, such as `rw [Real.log_mul (by assumption) (by assumption)]`, and closes the rewrite

### Requirement: Type-aware rendering
Rendering SHALL produce text that elaborates at the intended type:
- the outermost term is ascribed to the expected type, which is the problem's carrier unless the script names another;
- a sub-expression marked as computed in ℕ or ℤ (remainder, integer division, factorial, choose, gcd, ℕ subtraction) is rendered at that type and cast to the enclosing type;
- `Int.floor` and `Int.ceil` results are cast back where the enclosing type is a field.

#### Scenario: Natural remainder in a real goal
- **WHEN** a script renders the form of `((n % 7 : ℕ) : ℝ) + x` in a problem over ℝ
- **THEN** the text is `((n % 7 : ℕ) : ℝ) + x` (or an equivalent with the same casts), and it elaborates as a real number

#### Scenario: Rendering at a named type
- **WHEN** a script renders `x0 + 1` with `x0` of type ℕ and asks for type ℕ
- **THEN** the text is `(n + 1 : ℕ)`

### Requirement: Derivative proof terms
The toolkit SHALL build, from a Sage expression and a variable, a Lean `HasDerivAt` proof term composed from mathlib's derivative lemmas for constants, the variable, sums, products, quotients, powers, `exp`, `log`, `sqrt`, `sin`, `cos` and `rpow`. It SHALL pass the side conditions (nonzero denominators, `log` and `sqrt` arguments nonzero) from the domain conditions at the point, and fail naming any that are undischarged.

#### Scenario: Product with an exponential
- **WHEN** a script builds the derivative term of `x^2*exp(x)` at `1`
- **THEN** the term proves `HasDerivAt (fun x => x ^ 2 * Real.exp x) d 1` for a `d` that `ring_nf` or `norm_num` turns into `3 * Real.exp 1`

#### Scenario: Missing side condition
- **WHEN** a script builds the derivative term of `log(x)` at the atom `a` and nothing states `a ≠ 0`
- **THEN** the builder fails naming `a ≠ 0`
