/-
Veriphy's Lean test suite. `lake build VeriphyTest` builds all of it:

- `VeriphyTest.Kit` needs no Sage (extraction, closeAndEmit, replay, axiom guard);
- `VeriphyTest.SageRun` and `VeriphyTest.Benchmark` need Sage with `veriphy` installed.
-/
import VeriphyTest.Kit
import VeriphyTest.SageRun
import VeriphyTest.Benchmark
