## MODIFIED Requirements

### Requirement: Setup on first use
The first graph command that needs the reasoner or the checker SHALL set up the missing one from the pinned release
before it runs, print what it fetches or builds and where, and cache it, so installing Veriphy is the only installation
step. A later command SHALL find the cache and set up nothing.

#### Scenario: First reasoning run after installation
- **WHEN** `veriphy layers claims reason` runs right after `pip install veriphy`
- **THEN** it reports that it is setting up the reasoner and the checker, sets them up, and reports the run with the
  checker's verdict

#### Scenario: Second run
- **WHEN** the same command runs again
- **THEN** it sets up nothing and prints no setup message
