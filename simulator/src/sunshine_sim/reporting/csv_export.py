"""Tabular screening exports with spreadsheet formula-injection protection."""

import csv
import io


def screening_csv(rows: list[dict]) -> str:
    def safe(value):
        if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
            return "'" + value
        return value

    stream = io.StringIO()
    if rows:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow({k: safe(v) for k, v in row.items()})
    return stream.getvalue()
