from app.models import McqCheck, ReadAloudCheck


def test_grade_1_read_aloud_check_has_three_options_and_script():
    check = ReadAloudCheck.model_validate({'questions': [
        {'stem': 'Which shows three?', 'teacher_script': 'Show me three dots.', 'options': {'A': '●●●', 'B': '●●', 'C': '●●●●'}, 'correct_option': 'A', 'option_errors': {'B': {'description': 'counts two', 'ai_suggested': True}, 'C': {'description': 'counts four', 'ai_suggested': True}}}
    ] * 5})
    assert len(check.questions) == 5
    assert all(set(q.options) == {'A', 'B', 'C'} and q.teacher_script for q in check.questions)


def test_grade_3_check_has_four_options():
    check = McqCheck.model_validate({'questions': [
        {'stem': 'Value?', 'options': {'A': '4', 'B': '40', 'C': '43', 'D': '3'}, 'correct_option': 'B', 'option_errors': {k: {'description': 'error', 'ai_suggested': True} for k in ('A', 'C', 'D')}}
    ] * 5})
    assert all(set(q.options) == {'A', 'B', 'C', 'D'} for q in check.questions)
