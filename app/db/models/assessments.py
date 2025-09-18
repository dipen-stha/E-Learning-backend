from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel

from app.services.mixins.db_mixins import BaseTimeStampMixin


class AssessmentType(SQLModel, BaseTimeStampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(max_length=255)
    icon: str = Field(max_length=100)
    description: str

    assessments: list["Assessment"] = Relationship(back_populates="assessment_type")

    __tablename__ = "assessment_types"


class Assessment(SQLModel, BaseTimeStampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(max_length=255)
    assessment_type_id: int = Field(foreign_key="assessment_types.id")
    order: int | None = Field(nullable=True, ge=0)
    max_points: int = Field(default=0, ge=0)
    pass_points: int = Field(default=0, ge=0)
    subject_id: int = Field(foreign_key="subjects.id")
    description: str | None

    assessment_type: AssessmentType = Relationship(back_populates="assessments")
    questions: list["Question"] = Relationship(back_populates="assessment")
    subject: "Subject" = Relationship(back_populates="subject_assessments")
    assessment_sessions: list["StudentAssessmentSession"] = Relationship(
        back_populates="assessment"
    )

    __tablename__ = "assessments"


class Question(SQLModel, BaseTimeStampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True)
    assessment_id: int = Field(foreign_key="assessments.id")
    order: int = Field(ge=0, default=0)
    question: str

    assessment: Assessment = Relationship(back_populates="questions")
    options: list["Options"] = Relationship(back_populates="question")

    __tablename__ = "questions"


class Options(SQLModel, BaseTimeStampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True)
    question_id: int = Field(foreign_key="questions.id")
    text: str = Field(max_length=255)
    is_correct: bool = Field(default=False)

    question: Question = Relationship(back_populates="options")

    __tablename__ = "options"


class StudentAssessmentSession(SQLModel, BaseTimeStampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="users.id")
    assessment_id: int = Field(foreign_key="assessments.id")
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime | None = Field(nullable=True)
    score: float = Field(default=0.0)

    student: "User" = Relationship(back_populates="student_assessments")
    assessment: Assessment = Relationship(back_populates="assessment_sessions")

    __tablename__ = "student_assessment_sessions"
