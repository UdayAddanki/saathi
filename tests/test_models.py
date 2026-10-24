import pytest
from app.models import McqCheck, LessonPlan
def test_mcq_count():
 with pytest.raises(ValueError): McqCheck(questions=[])
def test_plan_minutes():
 with pytest.raises(ValueError): LessonPlan(title='x',learning_objectives=[],materials=[],sections=[],local_examples=[],differentiation_tips={'support':'','on_level':'','challenge':''},large_class_tips=[],homework_or_home_activity='')
