#!/bin/sh
# The research workflow end to end on the fixture chapter, from a workspace whose Lean export holds GraphTest.
# Usage: run.sh <python running veriphy>
set -eu
PY="$1"
FIXTURES="$(dirname "$0")"
mkdir -p .veriphy/graph/sources
cp "$FIXTURES/chapter.agent.ttl" .veriphy/graph/sources/chapter.agent.ttl
$PY -m veriphy layers claims validate
$PY -m veriphy layers claims reason
$PY -m veriphy layers claims levels --source chapter
$PY -m veriphy layers claims impact chapter metric-three | grep -q 'eq-2'
$PY -m veriphy layers claims slice chapter thm-3 | grep -q 'metric-three'
$PY -m veriphy layers claims appendix chapter --format latex
grep -q 'verdict entailed' .veriphy/graph/appendix/chapter.tex
echo 'research workflow: every step succeeded, appendix verdict entailed'
