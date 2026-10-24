from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field, model_validator

class Section(BaseModel):
    name: str
    minutes: int = Field(ge=0)
    teacher_actions: list[str]
    student_actions: list[str]
class Differentiation(BaseModel):
    support: str; on_level: str; challenge: str
class LessonPlan(BaseModel):
    title: str; learning_objectives: list[str]; concept_ids: list[str] = []; materials: list[str]
    sections: list[Section]; local_examples: list[str]; differentiation_tips: Differentiation
    large_class_tips: list[str]; homework_or_home_activity: str
    def has_valid_timing(self, period_minutes: int) -> bool:
        """Check timing against the selected class period."""
        return sum(section.minutes for section in self.sections) == period_minutes

    @model_validator(mode="after")
    def require_sections(self):
        """Reject an empty plan while allowing different class periods."""
        if not self.sections:
            raise ValueError("a plan needs timed sections")
        return self
class ErrorTag(BaseModel):
    misconception_id: str | None = None; description: str; ai_suggested: bool = False
    @model_validator(mode="after")
    def tag(self):
        if not self.ai_suggested and not self.misconception_id: raise ValueError("curated errors need an ID")
        return self
class Question(BaseModel):
    concept_id: str | None = None; stem: str; options: dict[str,str]; correct_option: Literal["A","B","C","D"]; option_errors: dict[str,ErrorTag]
    @model_validator(mode="after")
    def valid(self):
        if set(self.options) != {"A","B","C","D"}: raise ValueError("exactly four A-D options required")
        if set(self.option_errors) != set(self.options)-{self.correct_option}: raise ValueError("every wrong option needs an error")
        return self
class McqCheck(BaseModel):
    questions: list[Question]
    @model_validator(mode="after")
    def count(self):
        if len(self.questions) != 5: raise ValueError("exactly five questions required")
        return self
class ObservationTask(BaseModel):
    concept_id: str | None = None; task: str; materials: list[str]; what_success_looks_like: str; common_errors: list[ErrorTag]
class ObservationCheck(BaseModel):
    tasks: list[ObservationTask]
    @model_validator(mode="after")
    def count(self):
        if not 3 <= len(self.tasks) <= 5: raise ValueError("three to five tasks required")
        return self
class ReviewIssue(BaseModel):
    target: str; problem: str; fix: str
    severity: Literal["must_fix", "suggestion"]
class ReviewResult(BaseModel):
    passed: bool; issues: list[ReviewIssue]
class PlanRequest(BaseModel):
    class_id: str; subject: str; chapter_or_topic: str = Field(max_length=120); teacher_note: str | None = Field(default=None, max_length=500)
class ClassRequest(BaseModel):
    board: str; grade: int = Field(ge=1, le=5); section: str; class_size: int = Field(ge=1, le=100); period_minutes: int = 40; resources: list[str] = []

class Insight(BaseModel):
    check_id: str
    check_mode: Literal["each_child", "class_count"]
    concepts: list[dict]
    top_errors: list[dict]
    groups: dict
    missed_lesson: list[dict] = []
    prerequisite_flags: list[dict] = []
    recommended_actions: list[str] = []

class NextSteps(BaseModel):
    summary: str
    reteach: dict
    group_activities: list[dict]
    practice_sheet: list[dict]
    missed_lesson_catchup: str
    next_lesson_warmup: str

class ResultsRequest(BaseModel):
    check_mode: Literal["each_child", "class_count"]
    responses: list[dict] = []
    class_counts: dict | None = None
