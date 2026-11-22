# The `life-sciences` pack

The `life-sciences` pack checks claims about sequences and the terms that name biological entities. It reads FASTA
with Biopython, to check a sequence's length, GC fraction, motifs and translation, and reads ontologies in OBO with
pronto, so that `check-concepts` can check a source's terms against the Gene Ontology. It is the base of the
[`genomics`](genomics.md) pack.

```console
$ pip install 'veriphy[life-sciences]'
```

```yaml
# veriphy.yaml
version: 1
packs: [life-sciences]
```

## Sequences

The example, in
[`docs/examples/life-sciences/`](https://github.com/georgedouzas/veriphy/tree/main/docs/examples/life-sciences),
holds a 720-base coding sequence of a fluorescent protein:

```console
$ veriphy layers step check-sequence sequences.fasta --length 720 --gc 0.39 --motif GCTAGCAAAGGA --claim gfp-length
check-sequence sequences.fasta: accepted
  level: sequence-checked (checker)
$ veriphy layers step check-sequence sequences.fasta --length 717
check-sequence sequences.fasta: refused
  why: the length is 720, not 717
```

`--protein` checks the translation in the standard code, to the first stop, and `--record` picks a record other than
the first.

## Ontology terms

A source's concepts name ontology terms in the claim graph, by `owl:sameAs`:

```turtle
:bioluminescence a vp:Concept ; owl:sameAs <http://purl.obolibrary.org/obo/GO_0008218> .
```

```console
$ veriphy layers step check-concepts go-excerpt.obo
check-concepts go-excerpt.obo: conforms
  concepts: bioluminescence is "bioluminescence"
```

The ontology is any OBO or OWL file pronto reads, or a SKOS thesaurus.

## Steps, levels and conventions

| Step | Kind | Does | Grants |
|---|---|---|---|
| `check-sequence <fasta> [--length n] [--gc f] [--motif m] [--protein p]` | check | checks a sequence's properties | `sequence-checked` |
| `check-concepts <ontology>` | evidence | checks the source's concepts against the ontology | |

The conventions are `genome-assembly` (`GRCh37`, `GRCh38`) and `gene-nomenclature` (`hgnc-symbols`,
`ensembl-identifiers`).
