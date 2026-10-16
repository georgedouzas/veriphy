# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

<!-- insertion marker -->
## [0.3.0](https://github.com/georgedouzas/veriphy/releases/tag/0.3.0) - 2026-10-16

<small>[Compare with 0.2.0](https://github.com/georgedouzas/veriphy/compare/0.2.0...0.3.0)</small>

### Features

- sage_test fallback: claims tested at kernel-checked or oracle instances, independent of the claim, with levels, records, #veriphy_levels and the test_fallback recipe ([dcebd6e](https://github.com/georgedouzas/veriphy/commit/dcebd6e210b77ae568f58684d04fa3bb2333bb14) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- Linear-algebra certificates: independence, spans and kernels, matrix rank, dimensions (spans, intersections, kernels, products), non-linearity, signatures; packaging lemmas with the standard axioms ([7db47a6](https://github.com/georgedouzas/veriphy/commit/7db47a6a7bca718a50e612a2a523791dd14095de) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- definite_integral recipe: interval integrals in the translation, antiderivatives from Sage, endpoint facts at multiples of pi ([46cd156](https://github.com/georgedouzas/veriphy/commit/46cd156d92aa537df384da3b4d4159152cd85e1a) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- Trigonometric power-reduction, multiple-angle and Pythagorean rewrites in the core table; transcendental_rewrite tries every candidate ([715fdcb](https://github.com/georgedouzas/veriphy/commit/715fdcbb5120f310c0491b2488c412558d8c3315) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- matrix_from_goal for any size, transposes, vectors and side relations (cofactors over opaque functions) ([58adc27](https://github.com/georgedouzas/veriphy/commit/58adc27918323c68192405be847547ff62b8d2c4) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
- Replacement only for accepted blocks; vectors, named matrices and polynomials in the translation ([b083ac0](https://github.com/georgedouzas/veriphy/commit/b083ac02f5ef5c10ebeeaaf2f0b6d72bd2f998ce) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

### Bug Fixes

- Blocks declare the goals they leave open (rewrite steps); probes see integrals; typing ([15bbf0e](https://github.com/georgedouzas/veriphy/commit/15bbf0e02e681ad1ce62ad33a1e5b1adc5446992) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

### Docs

- Propose the book coverage change (recipes the KK/CSDR book needs) ([c84510d](https://github.com/georgedouzas/veriphy/commit/c84510d2369be800209ec09d48b7ee2f10f5fccc) by georgedouzas). Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

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

