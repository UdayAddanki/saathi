from __future__ import annotations

import re

def normalize_answer(value: str | None) -> str:
    return re.sub(r'\s+', ' ', str(value or '').strip().casefold())

def mark_answer(answer: str | None, question: dict) -> dict:
    """Mark only exact normalized answers; ambiguous text stays for teacher review."""
    if answer is None:
        return {'mark': None, 'status': '?'}
    expected = question.get('correct_answer')
    if not expected:
        return {'mark': None, 'status': '?'}
    correct = normalize_answer(answer) == normalize_answer(expected)
    if question.get('type') in {'fill_blank', 'short_answer'} and not correct:
        return {'mark': None, 'status': '?', 'suggestion': f"Probably correct: {answer}"}
    return {'mark': question.get('marks', 1) if correct else 0, 'status': '✓' if correct else '✗'}
