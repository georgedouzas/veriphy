"""Check claims about variants and reads with pysam, the Python interface to htslib.

`variant` checks that a variant is called in a VCF file, and, for a sample, its genotype. `coverage` recomputes the mean
depth of a region from the alignments, in SAM, BAM or CRAM, counting reads above a mapping quality.
"""

import re
from pathlib import Path

VARIANT = re.compile(r'^(?P<chrom>[^:\s]+):(?P<pos>\d+)\s*(?P<ref>[ACGTN]+)\s*>\s*(?P<alt>[ACGTN]+)$', re.IGNORECASE)
REGION = re.compile(r'^(?P<chrom>[^:\s]+):(?P<start>\d+)-(?P<end>\d+)$')


def _tools() -> list[dict[str, str]]:
    """Return pysam's version, as a record names it."""
    import pysam  # noqa: PLC0415 - the pack's optional library, imported only when the check runs

    return [{'name': 'pysam', 'version': pysam.__version__, 'pin': 'version'}]


def variant(inputs: dict[str, object]) -> dict[str, object]:
    """Check that a variant is called in a VCF file, and its genotype in a sample.

    Args:
        inputs: `vcf`, the file, `variant`, as `chr17:7674220 C>T` (1-based), and optionally `sample` and its claimed
            `genotype`, as `0/1`.

    Returns:
        `accepted` when the variant is in the file with the claimed genotype, `refused` otherwise.
    """
    import pysam  # noqa: PLC0415 - the pack's optional library, imported only when the check runs

    match = VARIANT.match(str(inputs['variant']).strip())
    if match is None:
        return {'status': 'failed', 'error': 'write the variant as chrom:position REF>ALT, such as chr17:7674220 C>T'}
    chrom, position = match['chrom'], int(match['pos'])
    ref, alt = match['ref'].upper(), match['alt'].upper()
    with pysam.VariantFile(str(inputs['vcf'])) as vcf:
        records = [r for r in vcf.fetch() if r.chrom == chrom and r.pos == position]
        samples = list(vcf.header.samples)
    called = next((r for r in records if r.ref == ref and alt in (r.alts or ())), None)
    found: dict[str, object] = {'chrom': chrom, 'pos': position, 'tools': _tools()}
    if called is None:
        there = ', '.join(f"{r.ref}>{','.join(r.alts or ())}" for r in records) or 'nothing'
        error = f'{chrom}:{position} has {there}, not {ref}>{alt}'
        return found | {'status': 'refused', 'errors': [{'message': error}]}
    sample = str(inputs.get('sample') or '')
    if not sample:
        return found | {'status': 'accepted', 'id': called.id}
    if sample not in samples:
        return {'status': 'failed', 'error': f"the file has no sample '{sample}': it has {', '.join(samples)}"}
    alleles = called.samples[sample]['GT']
    separator = '|' if called.samples[sample].phased else '/'
    genotype = separator.join('.' if a is None else str(a) for a in alleles)
    found |= {'sample': sample, 'genotype': genotype}
    claimed = str(inputs.get('genotype') or '')
    if claimed and sorted(claimed.replace('|', '/').split('/')) != sorted(genotype.replace('|', '/').split('/')):
        return found | {'status': 'refused', 'errors': [{'message': f'{sample} is {genotype}, not {claimed}'}]}
    return found | {'status': 'accepted'}


def coverage(inputs: dict[str, object]) -> dict[str, object]:
    """Recompute the mean depth of a region from the alignments.

    Args:
        inputs: `alignments`, a SAM, BAM or CRAM file, `region`, as `chr1:101-200` (1-based, inclusive), and
            `quality`, the least mapping quality a read needs to count (0 by default).

    Returns:
        The mean depth over the region, its least depth, and the reads counted.
    """
    import pysam  # noqa: PLC0415 - the pack's optional library, imported only when the check runs

    match = REGION.match(str(inputs['region']).strip())
    if match is None:
        return {'status': 'failed', 'error': 'write the region as chrom:start-end, such as chr1:101-200'}
    chrom, start, end = match['chrom'], int(match['start']) - 1, int(match['end'])
    quality = int(str(inputs.get('quality') or 0))
    depth = [0] * (end - start)
    reads = 0
    path = Path(str(inputs['alignments']))
    with pysam.AlignmentFile(str(path)) as alignments:
        if chrom not in alignments.references:
            known = ', '.join(alignments.references[:10])
            return {'status': 'failed', 'error': f"{path.name} has no reference '{chrom}': it has {known}"}
        # a SAM file has no index, so the reads are read through, not fetched
        for read in alignments.fetch(until_eof=True):
            if read.is_unmapped or read.reference_name != chrom or read.mapping_quality < quality:
                continue
            positions = [p for p in read.get_reference_positions() if start <= p < end]
            reads += bool(positions)
            for position in positions:
                depth[position - start] += 1
    mean = sum(depth) / len(depth)
    return {'status': 'reported', 'depth': mean, 'least': min(depth), 'reads': reads, 'tools': _tools()}
