from __future__ import annotations

import csv
import io
from pathlib import Path

LEVELS = {"low": "low", "mid": "mid", "high": "high", "l": "low", "m": "mid", "h": "high"}
OLD_LEVELS = {"ready": "high", "needs practice": "mid", "needs re-teaching": "low", "support": "low", "on level": "mid", "challenge": "high"}

def normalize_level(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip().casefold()
    return LEVELS.get(value, OLD_LEVELS.get(value))

def parse_roll_file(data: bytes, filename: str) -> list[dict]:
    """Parse CSV/XLSX without guessing missing readiness levels."""
    if filename.casefold().endswith('.csv'):
        rows = list(csv.DictReader(io.StringIO(data.decode('utf-8-sig'))))
    elif filename.casefold().endswith(('.xlsx', '.xlsm')):
        from openpyxl import load_workbook
        sheet = load_workbook(io.BytesIO(data), read_only=True, data_only=True).active
        values = list(sheet.values)
        headers = [str(value or '').strip().casefold() for value in values[0]]
        rows = [dict(zip(headers, row)) for row in values[1:]]
    else:
        raise ValueError('Upload a CSV or Excel file.')
    result = []
    for row in rows:
        normalized = {str(key).strip().casefold().replace('_', ' '): value for key, value in row.items()}
        level = normalize_level(str(normalized.get('readiness level') or ''))
        result.append({'roll_no': normalized.get('roll number') or normalized.get('roll no'), 'first_name': normalized.get('name'), 'readiness_level': level, 'valid': bool(normalized.get('roll number') or normalized.get('roll no')) and level is not None})
    return result
