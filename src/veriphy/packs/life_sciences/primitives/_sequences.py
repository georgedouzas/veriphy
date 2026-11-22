"""Check what a source claims about a sequence, with Biopython: its length, GC fraction, motifs and translation."""

from pathlib import Path

import Bio
from Bio import SeqIO
from Bio.SeqUtils import gc_fraction


def sequence(inputs: dict[str, object]) -> dict[str, object]:
    """Check a FASTA record against the properties a claim gives it.

    Args:
        inputs: `fasta`, the file, `record`, the record's identifier (the first record when empty), and any of
            `length`, `gc` (a fraction, compared to its reported digits), `motif` (present in the sequence) and
            `protein` (the translation of the sequence, with the standard code, up to the first stop codon).

    Returns:
        `accepted` when every given property holds, `refused` naming each that doesn't, with the properties found.
    """
    records = list(SeqIO.parse(str(inputs['fasta']), 'fasta'))
    wanted = str(inputs.get('record') or '')
    record = next((r for r in records if r.id == wanted), None) if wanted else (records[0] if records else None)
    if record is None:
        known = ', '.join(r.id for r in records[:10])
        return {
            'status': 'failed',
            'error': f"{Path(str(inputs['fasta'])).name} has no record '{wanted}': it has {known}",
        }
    seq = record.seq.upper()
    found: dict[str, object] = {'record': record.id, 'length': len(seq), 'gc': round(gc_fraction(seq), 6)}
    errors: list[str] = []
    if inputs.get('length') is not None and int(str(inputs['length'])) != len(seq):
        errors.append(f"the length is {len(seq)}, not {inputs['length']}")
    if inputs.get('gc') is not None:
        text = str(inputs['gc'])
        decimals = len(text.split('.', 1)[1]) if '.' in text else 0
        if abs(gc_fraction(seq) - float(text)) > 0.5 * 10.0**-decimals:
            errors.append(f'the GC fraction is {gc_fraction(seq):.4f}, not {text}')
    if inputs.get('motif'):
        motif = str(inputs['motif']).upper()
        found['motif_at'] = [i for i in range(len(seq)) if seq.startswith(motif, i)]
        if not found['motif_at']:
            errors.append(f'the motif {motif} is not in the sequence')
    if inputs.get('protein'):
        protein = str(seq.translate(to_stop=True))
        found['protein'] = protein
        if protein != str(inputs['protein']).upper():
            errors.append(f'the translation is {protein}, not {inputs["protein"]}')
    tools = [{'name': 'biopython', 'version': Bio.__version__, 'pin': 'version'}]
    status = 'refused' if errors else 'accepted'
    return {'status': status, **found, 'errors': [{'message': e} for e in errors], 'tools': tools}
