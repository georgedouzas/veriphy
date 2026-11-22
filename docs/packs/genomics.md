# The `genomics` pack

The `genomics` pack checks claims about variant calls and sequencing reads with pysam, the Python interface to
htslib: that a variant is called, with a sample's genotype, and the depth of a region. It builds on
[`life-sciences`](life_sciences.md).

```console
$ pip install 'veriphy[genomics]'
```

```yaml
# veriphy.yaml
version: 1
packs: [genomics]
```

## A first session

The example, in [`docs/examples/genomics/`](https://github.com/georgedouzas/veriphy/tree/main/docs/examples/genomics),
is synthetic: a 300-base reference, reads tiled across it, and three variants called in a patient and a control.

```console
$ veriphy layers step check-variant variants.vcf "chr1:120 C>T" --sample patient --genotype 1/1 --claim homozygous
check-variant variants.vcf: accepted
  level: genomic-data-checked (checker)
  record: .veriphy/runs/check-variant/….json
$ veriphy layers step check-variant variants.vcf "chr1:120 C>T" --sample control --genotype 1/1
check-variant variants.vcf: refused
  why: control is 0/1, not 1/1
  record: .veriphy/runs/check-variant/….json
```

Positions are 1-based, as in VCF. The depth of a region is recomputed from the alignments, in SAM, BAM or CRAM:

```console
$ veriphy layers step check-coverage reads.sam chr1:101-200 --claimed 20
check-coverage reads.sam: agrees
  found 20, the claim says 20 (tolerance 0.5)
  level: genomic-data-checked (checker)
  record: .veriphy/runs/check-coverage/….json
$ veriphy layers step check-coverage reads.sam chr1:101-200 --quality 30 --claimed 20
check-coverage reads.sam: differs from the claim
  found 15, the claim says 20 (tolerance 0.5)
  record: .veriphy/runs/check-coverage/….json
```

`--quality` counts only reads of at least that mapping quality, as a pipeline's filter does.

## Steps, levels and conventions

| Step | Kind | Does | Grants |
|---|---|---|---|
| `check-variant <vcf> <variant> [--sample s] [--genotype g]` | check | checks a variant call and a genotype | `genomic-data-checked` |
| `check-coverage <alignments> <region> [--quality q] [--claimed d]` | check | recomputes a region's mean depth | `genomic-data-checked` |

`genomic-data-checked` sits above `sequence-checked`. The convention `variant-coordinates` (`one-based-coordinates`,
`zero-based-coordinates`) lets claims say how they number positions: a claim resting on both is a clash.
