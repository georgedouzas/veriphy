/-
Tests for `#veriphy_graph`, Sage-free: claims with their levels, definitions, `uses` from proof terms, encoded names
and escaped statements, and the error for a prefix with no declarations.
-/
import Veriphy.Kit.Graph

namespace GraphTest

theorem plain : 1 + 1 = 2 := rfl

theorem certified : 2 + 2 = 4 := by veriphy_certified rfl

@[veriphy_tested kernel_test 3 0] theorem tested (n : Nat) : n + 0 = n := Nat.add_zero n

def metric : Nat := 3

theorem usesMetric : metric = 3 := rfl

def «α prop» : Prop := metric = 3 ∧ "a\"b" = "a\"b"

end GraphTest

set_option veriphy.graph.write false in
/--
info: 5 claims, 1 definitions, 2 dependencies
<urn:veriphy:lean:GraphTest.certified> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <urn:veriphy:vocabulary#Claim> .
<urn:veriphy:lean:GraphTest.certified> <urn:veriphy:vocabulary#leanName> "GraphTest.certified" .
<urn:veriphy:lean:GraphTest.certified> <urn:veriphy:vocabulary#statement> "2 + 2 = 4" .
<urn:veriphy:lean:GraphTest.certified> <urn:veriphy:vocabulary#hasLevel> <urn:veriphy:vocabulary#certificate> .
<urn:veriphy:lean:GraphTest.metric> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <urn:veriphy:vocabulary#Definition> .
<urn:veriphy:lean:GraphTest.metric> <urn:veriphy:vocabulary#leanName> "GraphTest.metric" .
<urn:veriphy:lean:GraphTest.metric> <urn:veriphy:vocabulary#statement> "Nat" .
<urn:veriphy:lean:GraphTest.plain> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <urn:veriphy:vocabulary#Claim> .
<urn:veriphy:lean:GraphTest.plain> <urn:veriphy:vocabulary#leanName> "GraphTest.plain" .
<urn:veriphy:lean:GraphTest.plain> <urn:veriphy:vocabulary#statement> "1 + 1 = 2" .
<urn:veriphy:lean:GraphTest.plain> <urn:veriphy:vocabulary#hasLevel> <urn:veriphy:vocabulary#lean-proof> .
<urn:veriphy:lean:GraphTest.tested> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <urn:veriphy:vocabulary#Claim> .
<urn:veriphy:lean:GraphTest.tested> <urn:veriphy:vocabulary#leanName> "GraphTest.tested" .
<urn:veriphy:lean:GraphTest.tested> <urn:veriphy:vocabulary#statement> "∀ (n : Nat), n + 0 = n" .
<urn:veriphy:lean:GraphTest.tested> <urn:veriphy:vocabulary#hasLevel> <urn:veriphy:vocabulary#kernel-test> .
<urn:veriphy:lean:GraphTest.usesMetric> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <urn:veriphy:vocabulary#Claim> .
<urn:veriphy:lean:GraphTest.usesMetric> <urn:veriphy:vocabulary#leanName> "GraphTest.usesMetric" .
<urn:veriphy:lean:GraphTest.usesMetric> <urn:veriphy:vocabulary#statement> "GraphTest.metric = 3" .
<urn:veriphy:lean:GraphTest.usesMetric> <urn:veriphy:vocabulary#hasLevel> <urn:veriphy:vocabulary#lean-proof> .
<urn:veriphy:lean:GraphTest.usesMetric> <urn:veriphy:vocabulary#uses> <urn:veriphy:lean:GraphTest.metric> .
<urn:veriphy:lean:GraphTest.%C2%AB%CE%B1%20prop%C2%BB> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <urn:veriphy:vocabulary#Claim> .
<urn:veriphy:lean:GraphTest.%C2%AB%CE%B1%20prop%C2%BB> <urn:veriphy:vocabulary#leanName> "GraphTest.«α prop»" .
<urn:veriphy:lean:GraphTest.%C2%AB%CE%B1%20prop%C2%BB> <urn:veriphy:vocabulary#statement> "GraphTest.metric = 3 ∧ \"a\\\"b\" = \"a\\\"b\"" .
<urn:veriphy:lean:GraphTest.%C2%AB%CE%B1%20prop%C2%BB> <urn:veriphy:vocabulary#hasLevel> <urn:veriphy:vocabulary#none> .
<urn:veriphy:lean:GraphTest.%C2%AB%CE%B1%20prop%C2%BB> <urn:veriphy:vocabulary#uses> <urn:veriphy:lean:GraphTest.metric> .
-/
#guard_msgs (info, error, drop warning) in
#veriphy_graph GraphTest

/-- error: no declarations start with Missing -/
#guard_msgs (info, error, drop warning) in
#veriphy_graph Missing
