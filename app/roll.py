from __future__ import annotations

import csv
import io
import zipfile
import xml.etree.ElementTree as ET
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
        try:
            from openpyxl import load_workbook
            sheet = load_workbook(io.BytesIO(data), read_only=True, data_only=True).active
            values = list(sheet.values)
        except ModuleNotFoundError:
            # Keep imports usable in a minimal install; openpyxl remains the
            # normal dependency and is declared in requirements.txt.
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                shared = []
                if 'xl/sharedStrings.xml' in archive.namelist():
                    root = ET.fromstring(archive.read('xl/sharedStrings.xml'))
                    ns = {'x': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                    shared = [''.join(t.text or '' for t in item.findall('.//x:t', ns)) for item in root.findall('x:si', ns)]
                root = ET.fromstring(archive.read('xl/worksheets/sheet1.xml'))
                ns = {'x': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                values = []
                for row in root.findall('.//x:sheetData/x:row', ns):
                    current = []
                    for cell in row.findall('x:c', ns):
                        value = cell.find('x:v', ns)
                        inline = cell.find('x:is', ns)
                        item = ''.join(t.text or '' for t in inline.findall('.//x:t', ns)) if inline is not None else (value.text if value is not None else '')
                        if cell.get('t') == 's' and item:
                            item = shared[int(item)]
                        current.append(item)
                    while len(current) < 3:
                        current.append('')
                    values.append(current)
        headers = [str(value or '').strip().casefold() for value in values[0]]
        rows = [dict(zip(headers, row)) for row in values[1:]]
    else:
        raise ValueError('Upload a CSV or Excel file.')
    result = []
    for row in rows:
        normalized = {str(key).strip().casefold().replace('_', ' '): value for key, value in row.items()}
        raw_level = str(normalized.get('readiness level') or '').strip()
        level = normalize_level(raw_level)
        roll_no = normalized.get('roll number') or normalized.get('roll no')
        if isinstance(roll_no, float) and roll_no.is_integer():
            roll_no = int(roll_no)
        elif isinstance(roll_no, str) and roll_no.isdigit():
            roll_no = int(roll_no)
        name = normalized.get('name')
        reasons = []
        if not name or not str(name).strip():
            reasons.append('name is missing')
        if not raw_level:
            reasons.append('readiness level is blank')
        elif level is None:
            reasons.append(f'unknown readiness level: {raw_level}')
        result.append({'roll_no': roll_no, 'first_name': name, 'readiness_level': level,
                       'valid': not reasons, 'errors': reasons})
    return result
