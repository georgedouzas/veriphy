/-
Primality by Pratt certificates, checked by kernel evaluation.

A certificate is a list of entries `(p, a, [(q₁, e₁), …])`: `p - 1 = ∏ qᵢ ^ eᵢ`, each `qᵢ` is 2 or the prime of an
earlier entry, `a ^ (p - 1) ≡ 1` and `a ^ ((p - 1) / qᵢ) ≢ 1 (mod p)`. Powers are computed by repeated squaring, so
the kernel never forms a large power. Soundness is mathlib's `lucas_primality`.
-/
import Mathlib.NumberTheory.LucasPrimality

namespace VeriphyCheck

/-- `a ^ k % m` by repeated squaring, for `k < 2 ^ fuel`. -/
def powMod (m : ℕ) : ℕ → ℕ → ℕ → ℕ
  | 0, _, _ => 1 % m
  | fuel + 1, a, k =>
    if k = 0 then 1 % m else
    let h := powMod m fuel (a * a % m) (k / 2)
    if k % 2 = 0 then h else a % m * h % m

theorem powMod_eq (m : ℕ) : ∀ fuel a k, k < 2 ^ fuel → powMod m fuel a k = a ^ k % m
  | 0, a, k, hk => by
    have : k = 0 := by simpa using hk
    simp [powMod, this]
  | fuel + 1, a, k, hk => by
    have hk2 : k / 2 < 2 ^ fuel := by rw [pow_succ] at hk; omega
    have ih := powMod_eq m fuel (a * a % m) (k / 2) hk2
    have hsq : (a * a % m) ^ (k / 2) ≡ a ^ (2 * (k / 2)) [MOD m] := by
      rw [pow_mul, sq]
      exact Nat.ModEq.pow _ (Nat.mod_modEq _ m)
    unfold powMod
    dsimp only
    split_ifs with h0 hev
    · simp [h0]
    · rw [ih]
      have : 2 * (k / 2) = k := by omega
      rw [this] at hsq
      exact hsq
    · rw [ih]
      have : 2 * (k / 2) + 1 = k := by omega
      have hmul : a % m * ((a * a % m) ^ (k / 2) % m) ≡ a * a ^ (2 * (k / 2)) [MOD m] :=
        Nat.ModEq.mul (Nat.mod_modEq a m) ((Nat.mod_modEq _ m).trans hsq)
      rw [← pow_succ', this] at hmul
      exact hmul

/-- The number of bits of `k`, enough fuel for `powMod`. -/
def bits (k : ℕ) : ℕ := Nat.log2 k + 1

theorem lt_two_pow_bits (k : ℕ) : k < 2 ^ bits k := by
  unfold bits
  rcases Nat.eq_zero_or_pos k with h | h
  · subst h; simp
  · exact Nat.lt_log2_self

/-- `a ^ k % m`. -/
def powModOf (m a k : ℕ) : ℕ := powMod m (bits k) a k

theorem powModOf_eq (m a k : ℕ) : powModOf m a k = a ^ k % m := powMod_eq m _ a k (lt_two_pow_bits k)

/-- `∏ q ^ e` over a factorization. -/
def factorProd (fs : List (ℕ × ℕ)) : ℕ := (fs.map fun f => f.1 ^ f.2).prod

/-- One certificate entry, given the primes already certified. -/
def entryCheck (known : List ℕ) (p a : ℕ) (fs : List (ℕ × ℕ)) : Bool :=
  2 ≤ p && factorProd fs == p - 1 && fs.all (fun f => f.1 == 2 || known.contains f.1) &&
    powModOf p a (p - 1) == 1 && fs.all fun f => powModOf p a ((p - 1) / f.1) != 1

/-- The whole certificate, entry by entry; returns the certified primes, or `none` at the first failure. -/
def prattPrimes : List (ℕ × ℕ × List (ℕ × ℕ)) → List ℕ → Option (List ℕ)
  | [], known => some known
  | (p, a, fs) :: rest, known => if entryCheck known p a fs then prattPrimes rest (p :: known) else none

/-- The certificate passes and certifies `P`. -/
def prattCheck (P : ℕ) (cert : List (ℕ × ℕ × List (ℕ × ℕ))) : Bool :=
  match prattPrimes cert [] with
  | some primes => primes.contains P
  | none => false

theorem prime_of_dvd_factorProd {fs : List (ℕ × ℕ)} (hfs : ∀ f ∈ fs, f.1.Prime) {q : ℕ} (hq : q.Prime)
    (hd : q ∣ factorProd fs) : ∃ f ∈ fs, q = f.1 := by
  induction fs with
  | nil => simp [factorProd] at hd; exact absurd hd hq.ne_one
  | cons f fs ih =>
    simp only [factorProd, List.map_cons, List.prod_cons] at hd
    rcases (Nat.Prime.dvd_mul hq).mp hd with h | h
    · exact ⟨f, by simp, (Nat.prime_dvd_prime_iff_eq hq (hfs f (by simp))).mp (hq.dvd_of_dvd_pow h)⟩
    · obtain ⟨g, hg, rfl⟩ := ih (fun g hg => hfs g (by simp [hg])) h
      exact ⟨g, by simp [hg], rfl⟩

theorem prime_of_entryCheck {known : List ℕ} (hk : ∀ q ∈ known, q.Prime) {p a : ℕ} {fs : List (ℕ × ℕ)}
    (h : entryCheck known p a fs = true) : p.Prime := by
  simp only [entryCheck, Bool.and_eq_true, beq_iff_eq, decide_eq_true_eq, List.all_eq_true, Bool.or_eq_true,
    List.contains_iff_mem, bne_iff_ne, ne_eq] at h
  obtain ⟨⟨⟨⟨hp, hprod⟩, hfac⟩, hfull⟩, hpart⟩ := h
  have hfsprime : ∀ f ∈ fs, f.1.Prime := fun f hf => by
    rcases hfac f hf with h2 | hmem
    · rw [h2]; exact Nat.prime_two
    · exact hk _ hmem
  have hp1 : 1 % p = 1 := Nat.mod_eq_of_lt (by omega)
  have hcast : ∀ k, ((a : ZMod p)) ^ k = 1 ↔ powModOf p a k = 1 := fun k => by
    rw [powModOf_eq, ← Nat.cast_pow, ← Nat.cast_one (R := ZMod p), ZMod.natCast_eq_natCast_iff', hp1]
  refine lucas_primality p a ((hcast _).mpr hfull) fun q hq hqd => ?_
  obtain ⟨f, hf, rfl⟩ := prime_of_dvd_factorProd hfsprime hq (hprod ▸ hqd)
  exact fun hpow => hpart f hf ((hcast _).mp hpow)

theorem prattPrimes_prime : ∀ (cert : List (ℕ × ℕ × List (ℕ × ℕ))) (known primes : List ℕ),
    (∀ q ∈ known, q.Prime) → prattPrimes cert known = some primes → ∀ q ∈ primes, q.Prime
  | [], known, primes, hk, h => by simp [prattPrimes] at h; subst h; exact hk
  | (p, a, fs) :: rest, known, primes, hk, h => by
    simp only [prattPrimes] at h
    split_ifs at h with he
    exact prattPrimes_prime rest (p :: known) primes
      (fun q hq => by
        rcases List.mem_cons.mp hq with rfl | hq
        · exact prime_of_entryCheck hk he
        · exact hk q hq) h

/-- `P` is prime, from a Pratt certificate the kernel checks. -/
theorem prime_of_pratt {P : ℕ} {cert : List (ℕ × ℕ × List (ℕ × ℕ))} (h : prattCheck P cert = true) : P.Prime := by
  unfold prattCheck at h
  split at h
  · rename_i primes hp
    exact prattPrimes_prime cert [] primes (by simp) hp P (List.contains_iff_mem.mp h)
  · simp at h

end VeriphyCheck
