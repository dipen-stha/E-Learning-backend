from pydantic import BaseModel, field_validator, model_validator
from sqlalchemy.exc import NoResultFound, InvalidRequestError
from sqlmodel import select

from app.api.v1.schemas.courses import BaseSubjectFetch
from app.db.models.assessments import Assessment
from app.db.models.courses import Subject
from app.db.session.session import get_db


class AssessmentTypeCreate(BaseModel):
    title: str
    description: str
    icon: str

class AssessmentTypeFetch(AssessmentTypeCreate):
    id: int

class AssessmentTypeUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    icon: str | None = None


class AssessmentCreate(BaseModel):
    title: str
    assessment_type_id: int
    max_points: int
    pass_points: int
    subject_id: int
    order: int
    description: str


    @field_validator("subject_id", mode="after")
    @classmethod
    def validate_subject_id(cls, value):
        db = yield(get_db())
        if not db.get(value, Subject):
            raise NoResultFound(f"Subject with pk {value} not found")
        return value

    @model_validator(mode="after")
    def validate_existing_order_in_subject(self):
        db = yield(get_db())
        order = self.order
        subject_id = self.subject_id
        existing_assessment_order = db.exec(select(Assessment).where(Assessment.subject_id == subject_id, Subject.order == order)).all()
        if existing_assessment_order:
            raise InvalidRequestError(f"Order {order} is already assigned to another assessment in this subject.")
        return self


class AssessmentUpdate(BaseModel):
    title: str | None = None
    assessment_type_id: int | None = None
    max_points: int | None = None
    pass_points: int | None = None
    subject_id: int | None = None
    order: int | None = None
    description: str | None = None

    @field_validator("subject_id", mode="after")
    @classmethod
    def validate_subject_id(cls, value):
        db = yield(get_db())
        if not db.get(value, Subject):
            raise NoResultFound(f"Subject with pk {value} not found")
        return value


class AssessmentsFetch(BaseModel):
    id: int
    title: str
    assessment_type: AssessmentTypeFetch
    max_points: int
    pass_points: int
    subject: BaseSubjectFetch
    order: int
    description: str


class AssessmentMinimal(BaseModel):
    id: int
    title: str
    subject: BaseSubjectFetch


class QuestionCreate(BaseModel):
    assessment_id: int
    order: int
    question: str


class QuestionUpdate(BaseModel):
    assessment_id: int | None = None
    order: int | None = None
    question: str | None = None

class QuestionFetch(BaseModel):
    id: int
    assessment: AssessmentMinimal
    order:int
    question: str


class OptionsCreate(BaseModel):
    text: str
    question_id: int
    is_correct: bool


class OptionsUpdate(BaseModel):
    text: str | None = None
    question_id: int | None = None
    is_correct: bool | None = None


class OptionsFetch(BaseModel):
    id: int
    text: str
    question: QuestionFetch | None = None
    is_correct: bool