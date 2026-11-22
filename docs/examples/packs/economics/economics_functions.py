"""The `economics` example pack's primitive: the mean of a column of a CSV file."""

import csv
from pathlib import Path


def mean(inputs: dict[str, object]) -> dict[str, object]:
    """Return the mean of a column of a CSV file, and how many rows it read.

    Args:
        inputs: `data`, the CSV file, and `column`, its column.

    Returns:
        The mean and the row count.
    """
    with Path(str(inputs['data'])).open(newline='') as handle:
        values = [float(row[str(inputs['column'])]) for row in csv.DictReader(handle)]
    return {'status': 'reported', 'mean': sum(values) / len(values), 'rows': len(values)}
