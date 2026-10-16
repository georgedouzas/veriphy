/-
Veriphy's Lean test suite. `lake build VeriphyTest` builds all of it:

- `VeriphyTest.Kit` needs no Sage (extraction, closeAndEmit, replay, axiom guard);
- `VeriphyTest.Check` needs no Sage (the VeriphyCheck checkers);
- `VeriphyTest.SageRun`, `VeriphyTest.SageTest` and `VeriphyTest.Benchmark` need Sage with `veriphy` installed.
-/
import VeriphyTest.Kit
import VeriphyTest.Check
import VeriphyTest.SageRun
import VeriphyTest.SageTest
import VeriphyTest.Benchmark
