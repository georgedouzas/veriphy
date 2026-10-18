# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

<!-- insertion marker -->
## [0.3.1](https://github.com/georgedouzas/veriphy/releases/tag/0.3.1) - 2026-10-18

<small>[Compare with 0.3.0](https://github.com/georgedouzas/veriphy/compare/0.3.0...0.3.1)</small>

### Bug Fixes

- Re-parse a replacement only when a line ends in ';' and the text is small ([da8bc16](https://github.com/georgedouzas/veriphy/commit/da8bc16c5c56a32ab5c3e517c48987aef6137cd1) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- Exact algebraic values in oracle instances, boolean edge flags, supplied proofs override stated conditions ([1267025](https://github.com/georgedouzas/veriphy/commit/12670258b9ea8c98713c15275fd202d3db6326d0) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- Translation and emission bugs found by the book's certification ([d9e241f](https://github.com/georgedouzas/veriphy/commit/d9e241f8d12300ee40fda5bda6aa8f9778cf5186) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

## [0.3.0](https://github.com/georgedouzas/veriphy/releases/tag/0.3.0) - 2026-10-16

<small>[Compare with 0.2.0](https://github.com/georgedouzas/veriphy/compare/0.2.0...0.3.0)</small>

### Features

- sage_test fallback: claims tested at kernel-checked or oracle instances, independent of the claim, with levels, records, #veriphy_levels and the test_fallback recipe ([afa84e6](https://github.com/georgedouzas/veriphy/commit/afa84e6d8e30167fdf23d4cb2f5aa9aac50fc4a4) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- Linear-algebra certificates: independence, spans and kernels, matrix rank, dimensions (spans, intersections, kernels, products), non-linearity, signatures; packaging lemmas with the standard axioms ([85758cf](https://github.com/georgedouzas/veriphy/commit/85758cf86bdd1a63bf878e6c21fcac78386be620) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- definite_integral recipe: interval integrals in the translation, antiderivatives from Sage, endpoint facts at multiples of pi ([824efd9](https://github.com/georgedouzas/veriphy/commit/824efd9701a42d2a668c39cb03ee6b74e8462892) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- Trigonometric power-reduction, multiple-angle and Pythagorean rewrites in the core table; transcendental_rewrite tries every candidate ([4e756a5](https://github.com/georgedouzas/veriphy/commit/4e756a5d8ea14250bc2b83b098e65ecccb4c1f02) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- matrix_from_goal for any size, transposes, vectors and side relations (cofactors over opaque functions) ([d9e00ec](https://github.com/georgedouzas/veriphy/commit/d9e00ec0b490ed37c75f9b24cb27b2fe9f367735) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- Replacement only for accepted blocks; vectors, named matrices and polynomials in the translation ([74abb66](https://github.com/georgedouzas/veriphy/commit/74abb6687b25a5567477d7cbfe6e5b40defd5eba) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

### Bug Fixes

- Endpoint values at zero by simp; the pilot's remaining goal shapes as tests; task 6.1 states Veriphy's part ([eab4d61](https://github.com/georgedouzas/veriphy/commit/eab4d616e331feba41edc492da2ef6ccd3ed6b27) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- Wrap the parsed block in veriphy_certified, keeping parse errors at the script's own columns ([1a803d2](https://github.com/georgedouzas/veriphy/commit/1a803d280020cb5f45691d43b88116c283d135d2) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- Align multi-line certified blocks; order-robust doctests; numpy as a Sage-provided module; coverage after book coverage ([08c2061](https://github.com/georgedouzas/veriphy/commit/08c2061a0377f3d367a343b36baa9719e8adba90) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- Blocks declare the goals they leave open (rewrite steps); probes see integrals; typing ([2c49ddc](https://github.com/georgedouzas/veriphy/commit/2c49ddc0325717a864614754b652a3e84c70ef07) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

### Docs

- Archive kk-csdr-book-coverage with its specs synced; README pins 0.3.0 ([afb5914](https://github.com/georgedouzas/veriphy/commit/afb5914f0b7bbbfb2b26dd609a7957818d8a3b3a) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- Test fallback and verification levels, linear algebra, matrix goals and integrals in the guide and the components page; changelog ([e88c563](https://github.com/georgedouzas/veriphy/commit/e88c563210b5e5238a50e9b8fd5388562a94a5bb) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- Propose the book coverage change (recipes the KK/CSDR book needs) ([b912a19](https://github.com/georgedouzas/veriphy/commit/b912a19bb01ae154387a056a4c1a41b821873fd7) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

### Chore

- Release 0.3.0 ([d85b562](https://github.com/georgedouzas/veriphy/commit/d85b5624e0af3df7039d18026c7105a1bbc08e7c) by georgedouzas).

## [0.2.0](https://github.com/georgedouzas/veriphy/releases/tag/0.2.0) - 2026-10-13

<small>[Compare with 0.1.0](https://github.com/georgedouzas/veriphy/compare/0.1.0...0.2.0)</small>

### Features

- Symbolic coverage: translation tables, coverage measurement, kernel checkers and components for Lie theory, representations, superalgebras, algebraic certificates, operators, geometry, summation, numerics and fusion categories ([2482bf8](https://github.com/georgedouzas/veriphy/commit/2482bf8efec7b52a277bf5df9e816662e01286f9) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

### Docs

- Pin the 0.2.0 release in the setup instructions ([1441ecb](https://github.com/georgedouzas/veriphy/commit/1441ecb00db4a0437ff6723d60e9b136f3bc1b04) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

### Chore

- Release 0.2.0 ([7dd25bc](https://github.com/georgedouzas/veriphy/commit/7dd25bcfe5eaec767577b7b412c60a105b5f344d) by georgedouzas).

## [0.1.0](https://github.com/georgedouzas/veriphy/releases/tag/0.1.0) - 2026-10-12

<small>[Compare with first commit](https://github.com/georgedouzas/veriphy/compare/1429e93b13a61dec8d7a6b6bdb0271bc346a56c1...0.1.0)</small>

### Docs

- Pin the first release, 0.1.0, in the setup instructions ([6aba0ca](https://github.com/georgedouzas/veriphy/commit/6aba0cac92951bd71d93b5ff3436bd72e534b8b3) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- record the founding design discussion as DESIGN.md ([5271a5e](https://github.com/georgedouzas/veriphy/commit/5271a5e4fa3bafe371bc1dd6f793ddfcd413417a) by georgedouzas). Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>

### Chore

- Release 0.1.0 ([e276264](https://github.com/georgedouzas/veriphy/commit/e276264c72e88389cbfe6414e3ad4d0f15873537) by georgedouzas).

