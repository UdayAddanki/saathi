from __future__ import annotations

import re

from .roll import normalize_level


def parse_roll_pdf(data: bytes) -> list[dict]:
    """Extract a typed, three-bucket roll without sending it to an AI model."""
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ValueError('PDF roll import needs the pypdf package.') from exc
    text = '\n'.join(page.extract_text() or '' for page in PdfReader(__import__('io').BytesIO(data)).pages)
    if not text.strip():
        raise ValueError('This PDF looks scanned. Please upload a typed PDF, Excel, or CSV.')
    current = None
    result = []
    for line in text.splitlines():
        heading = re.search(r'\b(high|mid|low)\s*(?:readiness)?\b', line, re.I)
        if heading and len(line.strip().split()) <= 3:
            current = normalize_level(heading.group(1))
            continue
        match = re.match(r'^\s*(\d+)\s*[.)-]?\s+(.+?)\s*$', line)
        if current and match:
            result.append({'roll_no': int(match.group(1)), 'first_name': match.group(2).strip(), 'readiness_level': current, 'valid': True, 'errors': []})
    if not result:
        raise ValueError('This PDF has no readable roll entries. Please upload a typed PDF, Excel, or CSV.')
    return result
