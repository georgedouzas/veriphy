# Translation coverage

This page records how much of real corpora Veriphy's symbolic translation covers, measured by `#veriphy_coverage`.
The command opens the binders of every theorem in the corpus, translates each relation (`=`, `≠`, `≤`, `<`, `≥`, `>`)
in its hypotheses and conclusion, and classifies every atom the translation needed:

- **local:** a variable, a numeral, or a structure projection of a variable (`x.val`, `p.1`);
- **uninterpreted:** a bundled map held in a variable, applied through its coercion (a plain local function `f x`
  translates as a Sage symbolic function since this release);
- **opaque:** a term headed by a global constant the translation does not know.

A statement is **fully covered** when every atom is local, and **covered up to uninterpreted functions** when no atom
is opaque. Statements with no relation are left out of the shares. Generated lemmas (`congr_simp`, `eq_def`, `eq_n`,
`injEq`, `inj`, `sizeOf_spec`) are not counted as statements.

## Reproducing

The runner is the Lake project `coverage/` in the repository. It requires Veriphy by path, Physlib at a pinned commit
whose dependencies match Veriphy's, and mathlib's `Archive`:

```sh
cd coverage
lake update && lake exe cache get
(cd .lake/packages/Physlib && LAKE_CONFIG=$PWD/lake-cache.toml \
  lake cache get --scope=physlib-master/leanprover-lean4-v4.34.1/physlib)
lake build Coverage
```

Each corpus writes its JSON report to `coverage/.veriphy/coverage/<prefix>.json`.

## Baseline (2026-10-12)

Measured before this release's new translation entries, at Veriphy commit `cf28d0c`, with Lean and
mathlib `v4.34.1`.

| Corpus | Theorems | With a relation | Fully covered | Up to uninterpreted | Failed |
|---|---|---|---|---|---|
| Physlib `master` at `0b252e14` | 7938 | 6051 | 6.7% | 7.9% | 0 |
| mathlib `Archive` (v4.34.1, `d13f23b7`) | 972 | 747 | 28.2% | 37.9% | 1 |
| mathlib `Mathlib.Analysis.ODE` | 119 | 69 | 15.9% | 37.7% | 0 |
| mathlib `Mathlib.Algebra.Lie` | 1625 | 1148 | 3.7% | 7.1% | 0 |
| mathlib `Mathlib.Geometry.Manifold` | 3033 | 1100 | 16.6% | 27.6% | 0 |

### Most frequent opaque heads

Each head is counted once per statement that needs it.

### Physlib `master` at `0b252e14`

| Rank | Head | Statements | Example |
|---|---|---|---|
| 1 | `DFunLike.coe` | 2005 | `Space.distGrad_eq_sum_basis` |
| 2 | `HSMul.hSMul` | 562 | `PauliMatrix.matrix_eq_scalar_add_vector` |
| 3 | `Finset.sum` | 352 | `Space.distGrad_eq_sum_basis` |
| 4 | `Subtype.val` | 243 | `FieldSpecification.CrAnSection.congr_fst` |
| 5 | `Norm.norm` | 135 | `LinearPMap.state_uncertainty_squared_of_raw_commutator` |
| 6 | `Inner.inner` | 131 | `Space.grad_inner_repr_eq` |
| 7 | `Time.deriv` | 102 | `ClassicalMechanics.SimplePendulum.deriv_cos_coord` |
| 8 | `WithLp.ofLp` | 88 | `Electromagnetism.DistElectromagneticPotential.gradLagrangian_sum_inr_i` |
| 9 | `TensorSpecies.τ` | 65 | `TensorSpecies.Tensor.prodT_contrT_fst` |
| 10 | `ite` | 64 | `Fermion.DualRightHandedWeyl.basis_apply` |
| 11 | `Space.val` | 62 | `ClassicalMechanics.SimplePendulum.spaceTrajectory_apply_one` |
| 12 | `minkowskiMatrix` | 56 | `minkowskiMatrix.as_block` |
| 13 | `ACCSystemLinear.LinSols.val` | 54 | `MSSMACC.B₃_val` |
| 14 | `Bracket.bracket` | 52 | `QuantumMechanics.angularMomentumSqr_commutation_lowering` |
| 15 | `MeasureTheory.integral` | 51 | `Polynomial.physHermite_orthogonal` |
| 16 | `Space.deriv` | 50 | `SpaceTime.deriv_sum_inr` |
| 17 | `FieldSpecification.crAnFieldOpToCreateAnnihilate` | 42 | `FieldSpecification.FieldOpFreeAlgebra.normalOrderF_mul_annihilate` |
| 18 | `Star.star` | 41 | `Physlib.Wirtinger.dWirtingerAntiDir_star_comp` |
| 19 | `PauliMatrix.pauliMatrix` | 40 | `PauliMatrix.σ1_σ1_trace` |
| 20 | `List.length` | 38 | `FieldSpecification.CrAnSection.eraseIdxEquiv_apply_snd` |
| 21 | `LinearPMap.toFun'` | 33 | `QuantumMechanics.angularMomentumDimThreeOperator_commutation` |
| 22 | `WickContraction.getDual?` | 33 | `WickContraction.insertAndContract_some_getDual?_self_eq` |
| 23 | `Bool.true` | 32 | `WickContraction.getDual?_get_self_neq` |
| 24 | `Finset.prod` | 31 | `WickContraction.joinSignRightExtra_eq_i_j_finset_eq_if` |
| 25 | `LinearPMap.domain` | 29 | `QuantumMechanics.angularMomentumRaisingOperator_domain_eq` |
| 26 | `NNReal.toReal` | 29 | `CanonicalEnsemble.differentialEntropy_eq_meanEnergy_sub_helmholtz_div_temp_add_correction` |
| 27 | `Option.isSome` | 29 | `WickContraction.getDual?_get_self_neq` |
| 28 | `CreateAnnihilate.annihilate` | 28 | `FieldSpecification.FieldOpFreeAlgebra.normalOrderF_mul_annihilate` |
| 29 | `Multiset.sum` | 28 | `FTheory.SU5.TenQuanta.decomposeFluxes_sum_of_noExotics` |
| 30 | `ClassicalMechanics.HarmonicOscillator.ω` | 27 | `ClassicalMechanics.DampedHarmonicOscillator.discriminant_eq_four_mul_m_sq_mul_decayRate_sq_sub_ω_sq` |

### mathlib `Archive` (v4.34.1, `d13f23b7`)

| Rank | Head | Statements | Example |
|---|---|---|---|
| 1 | `Finset.card` | 45 | `Imo2015Q6.b_pos` |
| 2 | `DFunLike.coe` | 39 | `Ballot.count_countedSequence` |
| 3 | `Imo2024Q3.Condition.N'` | 23 | `Imo2024Q3.Condition.p_apply_sub_two_le_p_apply` |
| 4 | `HSMul.hSMul` | 19 | `Imo2019Q2.Imo2019q2Cfg.two_zsmul_oangle_QQ₁A₂_eq_two_zsmul_oangle_QPA₂` |
| 5 | `Fintype.card` | 18 | `Imo1987Q1.mem_fiber` |
| 6 | `EuclideanGeometry.angle` | 16 | `Imo2001Q5.Setup.BAP_eq` |
| 7 | `Imo2024Q5.Path.firstMonster` | 15 | `Imo2024Q5.Path.firstMonster_eq_none` |
| 8 | `Compl.compl` | 13 | `VeroffAlgebra.compl_le_compl_iff_le` |
| 9 | `Imo2001Q5.Setup.x` | 13 | `Imo2001Q5.Setup.QB_by_AB` |
| 10 | `VeroffAlgebra.f` | 13 | `VeroffAlgebra.le_sup_left` |
| 11 | `Finset.sum` | 12 | `Theorems100.sum_lt_half_of_not_tendsto` |
| 12 | `Imo2024Q3.M` | 12 | `Imo2024Q3.Condition.lt_toFinset_card` |
| 13 | `Imo2024Q5.Strategy.play` | 12 | `Imo2024Q5.winningStrategy_play_one_eq_none_or_play_two_eq_none_of_not_edge` |
| 14 | `SingleShefferAlgebra.f` | 12 | `SingleShefferAlgebra.eq77` |
| 15 | `Imo2024Q3.Condition.N'aux` | 10 | `Imo2024Q3.Condition.N_add_one_lt_card_filter_eq_of_small_of_N'aux_le` |
| 16 | `List.length` | 10 | `Imo2024Q5.Path.one_lt_length_cells` |
| 17 | `Nat.nth` | 10 | `Imo2024Q3.Condition.apply_nth_add_one_eq_of_lt` |
| 18 | `Option.none` | 9 | `Imo2024Q5.winningStrategy_play_one_eq_none_or_play_two_eq_none_of_not_edge` |
| 19 | `closure` | 9 | `Topology.ClosureCompl.kckckc_fourteenSet` |
| 20 | `Option.some` | 8 | `Imo2024Q5.Path.mem_of_firstMonster_eq_some` |
| 21 | `Theorems100.«82».Cube.b` | 8 | `Theorems100.«82».Cube.head_shiftUp` |
| 22 | `Theorems100.«82».Cube.w` | 8 | `Theorems100.«82».mi_strict_minimal` |
| 23 | `Fin.val` | 7 | `Imo2024Q5.winningStrategy_play_one_eq_none_or_play_two_eq_none_of_not_edge` |
| 24 | `Imo2019Q2.Imo2019q2Cfg.A₂` | 7 | `Imo2019Q2.Imo2019q2Cfg.A₂_ne_P` |
| 25 | `Nat.factorial` | 7 | `Imo1987Q1.card_fixed_points` |
| 26 | `Prod.fst` | 7 | `Imo2024Q5.find?_eq_eq_find?_le` |
| 27 | `Set.ofPred` | 7 | `Konigsberg.setOf_odd_degree_eq` |
| 28 | `IfExpr.eval` | 6 | `IfExpr.eval_lit` |
| 29 | `Imo2024Q2.Condition.N` | 6 | `Imo2024Q2.Condition.N_spec` |
| 30 | `Imo2024Q3.Condition.k` | 6 | `Imo2024Q3.Condition.k_lt_card_filter_eq_of_small_of_N'aux_le` |

### mathlib `Mathlib.Analysis.ODE`

| Rank | Head | Statements | Example |
|---|---|---|---|
| 1 | `NNReal.toReal` | 14 | `dist_le_of_trajectories_ODE_of_mem` |
| 2 | `Dist.dist` | 11 | `dist_le_of_trajectories_ODE_of_mem` |
| 3 | `ODE.FunSpace.toFun` | 10 | `ODE.FunSpace.apply_of_zero` |
| 4 | `Max.max` | 8 | `ODE.FunSpace.dist_iterate_next_iterate_next_le` |
| 5 | `ODE.picard` | 8 | `ODE.contDiffOn_nat_picard_Icc` |
| 6 | `gronwallBound` | 7 | `le_gronwallBound_of_liminf_deriv_right_le` |
| 7 | `Nat.factorial` | 5 | `ODE.FunSpace.dist_comp_iterate_next_le` |
| 8 | `Norm.norm` | 4 | `norm_le_gronwallBound_of_norm_deriv_right_le` |
| 9 | `Finset.sum` | 3 | `discrete_gronwall_prod_general` |
| 10 | `ODE.FunSpace.compProj` | 3 | `ODE.FunSpace.compProj_val` |
| 11 | `DFunLike.coe` | 1 | `ODE.FunSpace.toContinuousMap_apply_eq_apply` |
| 12 | `Finset.prod` | 1 | `discrete_gronwall_prod_general` |
| 13 | `Set.ofPred` | 1 | `ODE.FunSpace.range_toContinuousMap` |
| 14 | `Set.range` | 1 | `ODE.FunSpace.range_toContinuousMap` |
| 15 | `intervalIntegral` | 1 | `ODE.picard_apply` |

### mathlib `Mathlib.Algebra.Lie`

| Rank | Head | Statements | Example |
|---|---|---|---|
| 1 | `DFunLike.coe` | 259 | `LieAlgebra.ad_lie` |
| 2 | `Bracket.bracket` | 187 | `lie_sum` |
| 3 | `Bot.bot` | 118 | `LieAlgebra.abelian_iff_derived_one_eq_bot` |
| 4 | `Top.top` | 64 | `LieSubmodule.iSup_toSubmodule_eq_top` |
| 5 | `HSMul.hSMul` | 60 | `LieAlgebra.IsKilling.chainLength_nsmul` |
| 6 | `LieSubmodule.toSubmodule` | 45 | `LieSubmodule.toSubmodule_mk` |
| 7 | `Subtype.val` | 42 | `LieEquiv.lieSubalgebraMap_apply` |
| 8 | `SetLike.coe` | 38 | `LieModule.coe_lowerCentralSeries_eq_int` |
| 9 | `LieModule.genWeightSpace` | 35 | `LieModule.LinearWeights.map_add` |
| 10 | `LieSubmodule.map` | 33 | `LieSubmodule.map_le_iff_le_comap` |
| 11 | `iSup` | 27 | `LieSubmodule.iSup_toSubmodule_eq_top` |
| 12 | `LieModule.lowerCentralSeries` | 23 | `LieModule.isNilpotent_iff` |
| 13 | `Max.max` | 22 | `LieSubmodule.span_union` |
| 14 | `LieIdeal.map` | 21 | `LieIdeal.map_of_image` |
| 15 | `LieAlgebra.derivedSeries` | 16 | `LieAlgebra.derivedSeries_def` |
| 16 | `LieAlgebra.derivedSeriesOfIdeal` | 16 | `LieAlgebra.abelian_iff_derived_one_eq_bot` |
| 17 | `LieAlgebra.rootSpace` | 16 | `LieAlgebra.rootSpace_zero_eq` |
| 18 | `LieHom.comp` | 16 | `LieHom.prod_comp` |
| 19 | `LieSubalgebra.toSubmodule` | 16 | `LieSubalgebra.toSubmodule_mk` |
| 20 | `LieHom.range` | 15 | `LieSubalgebra.incl_range` |
| 21 | `LieSubalgebra.lieSpan` | 15 | `LieSubalgebra.span_union` |
| 22 | `Min.min` | 15 | `LieSubmodule.normalizer_inf` |
| 23 | `LieAlgebra.center` | 14 | `LieAlgebra.abelian_of_le_center` |
| 24 | `LieModule.chainTopCoeff` | 14 | `LieAlgebra.IsKilling.chainTopCoeff_of_eq_zsmul_add` |
| 25 | `LieSubmodule.comap` | 14 | `LieSubmodule.map_le_iff_le_comap` |
| 26 | `LieSubmodule.ucs` | 14 | `LieSubalgebra.ucs_eq_self_of_isCartanSubalgebra` |
| 27 | `LieIdeal.toLieSubalgebra` | 13 | `LieHom.range_inl` |
| 28 | `LieModule.chainBotCoeff` | 13 | `LieAlgebra.IsKilling.chainBotCoeff_zero_right` |
| 29 | `Module.finrank` | 13 | `LieAlgebra.engel_isBot_of_isMin.lieCharpoly_coeff_natDegree` |
| 30 | `Submodule.span` | 13 | `LieSubalgebra.submodule_span_le_lieSpan` |

### mathlib `Mathlib.Geometry.Manifold`

| Rank | Head | Statements | Example |
|---|---|---|---|
| 1 | `DFunLike.coe` | 117 | `mfderiv_prod_eq_add_apply` |
| 2 | `mfderivWithin` | 43 | `MDifferentiableWithinAt.mfderivWithin_mono_of_mem_nhdsWithin` |
| 3 | `mfderiv` | 42 | `inverse_mfderiv_add_left` |
| 4 | `ContinuousLinearMap.comp` | 38 | `mvfderiv_comp_mfderivWithin_of_eq` |
| 5 | `Set.preimage` | 38 | `Manifold.IsImmersionAtOfComplement.mk_of_charts` |
| 6 | `HSMul.hSMul` | 36 | `const_smul_mfderiv` |
| 7 | `VectorField.mlieBracketWithin` | 29 | `VectorField.mlieBracketWithin_congr` |
| 8 | `PartialEquiv.source` | 26 | `contMDiffOn_iff_of_subset_source'` |
| 9 | `PartialEquiv.target` | 25 | `ModelWithCorners.extChartAt_transContinuousLinearEquiv_target` |
| 10 | `Set.range` | 24 | `range_euclideanQuadrant` |
| 11 | `Set.univ` | 24 | `mdifferentiable_of_mdifferentiableOn_iUnion_of_isOpen` |
| 12 | `nhdsWithin` | 24 | `OpenPartialHomeomorph.map_extend_nhdsWithin_eq_image` |
| 13 | `Filter.map` | 23 | `map_extChartAt_nhds_of_boundaryless` |
| 14 | `ContinuousLinearMap.id` | 22 | `mfderiv_sumInl` |
| 15 | `Set.image` | 22 | `Manifold.IsImmersionAt.map_target_subset_target` |
| 16 | `VectorField.mlieBracket` | 20 | `Filter.EventuallyEq.mlieBracket_vectorField_eq` |
| 17 | `mvfderivWithin` | 20 | `mvfderiv_comp_mfderivWithin_of_eq` |
| 18 | `Function.support` | 18 | `SmoothBumpCovering.support_toSmoothPartitionOfUnity_subset` |
| 19 | `OpenPartialHomeomorph.toFun'` | 18 | `TangentBundle.coe_chartAt_symm_fst` |
| 20 | `mvfderiv` | 18 | `mvfderiv_fun_neg` |
| 21 | `CategoryTheory.CategoryStruct.comp` | 17 | `smoothSheafCommRing.forgetStalk_hom_comp_evalHom_assoc` |
| 22 | `chartAt` | 17 | `chartAt_self_eq` |
| 23 | `PartialEquiv.toFun` | 16 | `modelWithCornersEuclideanQuadrant_symm_apply_of_le` |
| 24 | `Manifold.pathELength` | 15 | `Manifold.exists_lt_of_riemannianEDist_lt` |
| 25 | `Set.ofPred` | 15 | `setOfPred_riemannianEDist_lt_subset_nhds` |
| 26 | `Inter.inter` | 14 | `IsLocalDiffeomorphOn.preimage_boundary_inter` |
| 27 | `ModelWithCorners.boundary` | 14 | `Diffeomorph.preimage_boundary` |
| 28 | `Norm.norm` | 13 | `stereo_right_inv` |
| 29 | `WithTop.some` | 13 | `VectorField.eventually_contMDiffWithinAt_mpullbackWithin_extChartAt_symm` |
| 30 | `Prod.mk` | 12 | `equivTangentBundleProd_symm_apply_snd` |
