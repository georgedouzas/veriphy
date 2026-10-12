# Spec Delta

## MODIFIED Requirements

### Requirement: Render symbolic expressions
The toolkit SHALL render Sage symbolic-ring expressions, rational functions and matrices as Lean terms over the problem's atoms, through an explicit function table:
- `sqrt`, `exp`, `log`, `sin`, `cos`, `tan` → their `Real` versions (`Complex` for ℂ);
- `cosh`, `sinh`, `tanh`, `arctan`, `arcsin`, `arccos` → their `Real` versions, and `log(x)/log(b)` written by the script as `logb(b, x)` → `Real.logb b x`;
- a power with a non-integer exponent → `Real.rpow` notation `x ^ (y : ℝ)`;
- `factorial`, `binomial`, `gcd`, `floor`, `ceil` → `Nat.factorial`, `Nat.choose`, `Nat.gcd`/`Int.gcd`, `Int.floor`, `Int.ceil`;
- `pi` → `Real.pi`, `I` → `Complex.I`;
- `abs` → `|·|`;
- matrices → `!![…]` literals;
- every entry of the project's translation tables.

An unmapped function SHALL be rejected with an error naming it and pointing at the project translation tables.

#### Scenario: Absolute value of a real
- **WHEN** a script renders `abs(x0 - 1)` with `x0` a real atom
- **THEN** the text is `|x - 1|`, never `Int.natAbs`

#### Scenario: Complex exponential
- **WHEN** a script renders `exp(x0)` with `x0` a complex atom
- **THEN** the text is `Complex.exp z`

#### Scenario: Unmapped function
- **WHEN** a script renders `gamma(x0)` and no project entry maps `gamma`
- **THEN** the toolkit raises an error naming `gamma` and the `translations/` directory

#### Scenario: Project entry
- **WHEN** the project has an entry mapping Sage `cosh` to `Real.cosh` and a script renders `cosh(x0)`
- **THEN** the text is `Real.cosh x`

### Requirement: Rewrite chains with named lemmas
The toolkit SHALL build rewrite and `calc` steps justified by named mathlib lemmas, passing the lemma's side conditions from the domain conditions. It SHALL provide one rewrite table, made of the core entries (`Real.exp_add`, `Real.exp_log`, `Real.log_exp`, `Real.log_mul`, `Real.log_div`, `Real.log_rpow`, `Real.sqrt_mul_self`, `Real.sin_sq_add_cos_sq`, `Real.cosh_sq` and similar) and the project's entries. Each entry names the functions it applies to and its side conditions. Scripts and recipes SHALL select rewrites from that table rather than keep their own.

#### Scenario: Exponential identity
- **WHEN** a script proves `Real.exp a * Real.exp b = Real.exp (a + b)` with a rewrite by `Real.exp_add`
- **THEN** the emitted step is `rw [← Real.exp_add]` (or equivalent), and it closes the goal

#### Scenario: Side condition from the table
- **WHEN** a script selects `Real.log_mul` for `Real.log (x * y)` and the context has `hx : x ≠ 0` and `hy : y ≠ 0`
- **THEN** the emitted step is `rw [Real.log_mul hx hy]`

## ADDED Requirements

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
