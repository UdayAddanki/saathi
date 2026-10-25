from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field, model_validator

class Section(BaseModel):
    name: str
    minutes: int = Field(ge=0)
    teacher_actions: list[str]
    student_actions: list[str]

class Exchange(BaseModel):
    teacher: str
    students: str

class MethodStep(BaseModel):
    name: str
    minutes: int = Field(ge=0)
    purpose: str
    materials: list[str] = []
    exchanges: list[Exchange]
    check_for_understanding: str | None = None
    tiered_exchanges: dict[str, list[Exchange]] | None = None

class KeyWord(BaseModel):
    word: str
    meaning: str
    introduction: str

class WrongResponse(BaseModel):
    response: str
    tells_teacher: str
    misconception_id: str | None = None

class LessonVision(BaseModel):
    objective: str
    why_this_objective: str
    assessment: str
    expected_student_response: dict
    key_words: list[KeyWord]
    differentiation_plan: dict | None = None
    @model_validator(mode="after")
    def valid_vision(self):
        if not self.objective.startswith("Students will be able to"):
            raise ValueError("objective must start with Students will be able to")
        if not 3 <= len(self.key_words) <= 6:
            raise ValueError("there must be 3 to 6 key words")
        return self

class ProjectOutline(BaseModel):
    driving_question: str
    final_product: str
    days: list[str]
    today_day: int = Field(ge=1)
    total_days: int = Field(ge=1)
    @model_validator(mode="after")
    def valid_day(self):
        if self.today_day > self.total_days or len(self.days) != self.total_days:
            raise ValueError("project day must be within the total days")
        return self

class MakeItWork(BaseModel):
    differentiation: dict
    large_class_tips: list[str]
    local_examples: list[str]
    home_activity: str

LESSON_STEPS = {
    "5-step": ["Opening", "I do", "We do", "You do", "Closing"],
    "5E": ["Engage", "Explore", "Explain", "Elaborate", "Evaluate"],
    "project-based": ["Launch or recap", "Work time", "Check-in", "Share", "Reflect + assess"],
    "experiential": ["Do", "Reflect", "Think", "Apply", "Assess"],
    "5-magic": ["Purpose", "Integration", "Mastery", "Methods", "Partnership"],
}
class Differentiation(BaseModel):
    support: str; on_level: str; challenge: str
class LessonPlan(BaseModel):
    lesson_type: Literal["5-step", "5E", "project-based", "experiential", "5-magic"] | None = None
    vision: LessonVision | None = None
    method: list[MethodStep] | None = None
    make_it_work: MakeItWork | None = None
    project_outline: ProjectOutline | None = None
    differentiated: bool = False
    differentiation_types: list[Literal["content", "process", "product"]] = []
    title: str | None = None
    learning_objectives: list[str] = []
    concept_ids: list[str] = []
    materials: list[str] = []
    sections: list[Section] = []
    local_examples: list[str] = []
    differentiation_tips: Differentiation | None = None
    large_class_tips: list[str] = []
    homework_or_home_activity: str = ""
    def has_valid_timing(self, period_minutes: int) -> bool:
        """Check timing against the selected class period."""
        steps = self.method if self.method is not None else self.sections
        return sum(step.minutes for step in steps) == period_minutes

    @model_validator(mode="after")
    def require_sections(self):
        """Reject an empty plan while allowing different class periods."""
        if self.method is not None:
            if not self.lesson_type or [step.name for step in self.method] != LESSON_STEPS[self.lesson_type]:
                raise ValueError("lesson steps do not match the lesson type")
            if any(not step.exchanges for step in self.method) or any(not exchange.teacher or not exchange.students for step in self.method for exchange in step.exchanges):
                raise ValueError("every method step needs teacher and student exchanges")
            if self.lesson_type == "project-based" and self.project_outline is None:
                raise ValueError("project lessons need a project outline")
        elif not self.sections:
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
    class_id: str
    subject: str
    chapter_or_topic: str | None = Field(default=None, max_length=120)
    chapter: str = Field(default="", max_length=120)
    topic: str = Field(default="", max_length=120)
    lesson_type: Literal["5-step", "5E", "project-based", "experiential", "5-magic"] = "5-step"
    learning_level_choice: str = "Mixed levels"
    learning_level_text: str = Field(default="", max_length=300)
    unit_goal: str = Field(default="", max_length=300)
    current_situation: str = Field(default="", max_length=500)
    classroom_vision: str = Field(default="", max_length=300)
    differentiated: bool = False
    differentiation_types: list[Literal["content", "process", "product"]] = []
    use_last_groups: bool = False
    day_number: int = Field(default=1, ge=1)
    total_days: int = Field(default=1, ge=1)
    project_idea: str = Field(default="", max_length=200)
    project_scope: Literal["daily", "whole_project"] = "daily"
    teacher_note: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def normalize_topic(self):
        if not self.topic:
            self.topic = self.chapter_or_topic or self.chapter
        return self
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
