from sqlalchemy.exc import InvalidRequestError, NoResultFound
from sqlalchemy.orm import joinedload, selectinload
from sqlmodel import Session, delete, select

from app.api.v1.schemas.assessments import (
    AssessmentCreate,
    AssessmentMinimal,
    AssessmentsFetch,
    AssessmentTypeCreate,
    AssessmentTypeFetch,
    AssessmentTypeUpdate,
    AssessmentUpdate,
    OptionsFetch,
    QuestionCreate,
    QuestionFetch,
    QuestionUpdate,
)
from app.api.v1.schemas.courses import BaseCourse, BaseSubjectFetch
from app.db.models.assessments import Assessment, AssessmentType, Options, Question
from app.db.models.courses import Course, Subject
from app.services.utils.crud_utils import update_model_instance


def create_assessment_type(assessment_type: AssessmentTypeCreate, db: Session):
    try:
        assessment_data = assessment_type.model_dump()
        assessment_instance = AssessmentType(**assessment_data)
        db.add(assessment_instance)
        db.commit()
        db.refresh(assessment_instance)
        return assessment_instance
    except Exception as e:
        db.rollback()
        raise e


def update_assessment_type(
    assessment_type_id: int, assessment_type: AssessmentTypeUpdate, db: Session
):
    try:
        assessment_instance = db.get(assessment_type_id, AssessmentType)
        if not assessment_instance:
            raise NoResultFound(f"Assessment with pk {assessment_type_id} not found")
        subject_id = assessment_type.subject_id
        if not db.get(subject_id, Subject):
            raise NoResultFound(f"Subject with pk {subject_id} not found")
        assessment_data = assessment_type.model_dump()
        updated_assessment_instance = update_model_instance(
            assessment_instance, assessment_data
        )
        db.add(updated_assessment_instance)
        db.commit()
        db.refresh(updated_assessment_instance)
        return updated_assessment_instance
    except Exception as e:
        db.rollback()
        raise e


def fetch_all_assessment_types(db: Session):
    try:
        statement = select(AssessmentType)
        all_assessment_type = db.exec(statement).all()
        return [
            AssessmentTypeFetch(
                id=assessment_type.id,
                title=assessment_type.title,
                icon=assessment_type.icon,
                description=assessment_type.description,
            )
            for assessment_type in all_assessment_type
        ]
    except Exception as e:
        raise e


def fetch_assessment_type_by_id(type_id: int, db: Session):
    type_instance = db.exec(
        select(AssessmentType).where(AssessmentType.id == type_id)
    ).first()
    return AssessmentTypeFetch(
        id=type_instance.id,
        title=type_instance.title,
        description=type_instance.description,
        icon=type_instance.icon,
    )


def create_assessment(assessment_create: AssessmentCreate, db: Session):
    try:
        assessment_data = assessment_create.model_dump()
        assessment_instance = Assessment(**assessment_data)
        db.add(assessment_instance)
        db.commit()
        db.refresh(assessment_instance)
        return assessment_instance
    except Exception as e:
        db.rollback()
        raise e


def update_assessment(assessment_id: int, assessment: AssessmentUpdate, db: Session):
    try:
        assessment_instance = db.get(Assessment, assessment_id)
        if not assessment_instance:
            raise NoResultFound(f"Assessment with pk {assessment_id} not found")
        subject_id = assessment.subject_id
        order = assessment.order
        existing_order_assessment = db.exec(
            select(Assessment).where(
                Assessment.subject_id == subject_id,
                Assessment.order == order,
                Assessment.id != assessment_id,
            )
        ).all()
        if existing_order_assessment:
            raise InvalidRequestError(f"Assessment with order {order} already exists")
        assessment_data = assessment.model_dump()
        updated_assessment_instance = update_model_instance(
            assessment_instance, assessment_data
        )
        db.add(updated_assessment_instance)
        db.commit()
        db.refresh(updated_assessment_instance)
        return updated_assessment_instance
    except Exception as e:
        db.rollback()
        raise e


def fetch_all_assessments(db: Session):
    try:
        statement = (
            select(Assessment)
            .options(
                joinedload(Assessment.assessment_type),
                joinedload(Assessment.subject).joinedload(Subject.course),
                selectinload(Assessment.questions),
            )
            .order_by(Assessment.id.desc())
        )
        assessment_instances = db.exec(statement).all()
        return [
            AssessmentsFetch(
                id=assessment.id,
                title=assessment.title,
                assessment_type=AssessmentTypeFetch(
                    id=assessment.assessment_type.id,
                    title=assessment.assessment_type.title,
                    description=assessment.assessment_type.description,
                    icon=assessment.assessment_type.icon,
                ),
                max_points=assessment.max_points,
                pass_points=assessment.pass_points,
                subject=BaseSubjectFetch(
                    id=assessment.subject.id, title=assessment.subject.title
                ),
                order=assessment.order,
                description=assessment.description,
                course=BaseCourse(
                    id=assessment.subject.course.id,
                    title=assessment.subject.course.title,
                ),
            )
            for assessment in assessment_instances
        ]
    except Exception as e:
        raise e


def assessment_by_id(assessment_id: int, db: Session):
    statement = (
        select(Assessment, AssessmentType, Course, Subject)
        .join(Subject, Assessment.subject_id == Subject.id)
        .join(AssessmentType, Assessment.assessment_type_id == AssessmentType.id)
        .join(Course, Subject.course_id == Course.id)
        .where(Assessment.id == assessment_id)
    )
    assessment_instance, assessment_type, course, subject = db.exec(statement).first()
    return AssessmentsFetch(
        id=assessment_instance.id,
        title=assessment_instance.title,
        assessment_type=AssessmentTypeFetch(
            id=assessment_type.id,
            title=assessment_type.title,
            description=assessment_type.description,
            icon=assessment_type.icon,
        ),
        course=BaseCourse(id=course.id, title=course.title),
        subject=BaseSubjectFetch(id=subject.id, title=subject.title),
        max_points=assessment_instance.max_points,
        pass_points=assessment_instance.pass_points,
        order=assessment_instance.order,
        description=assessment_instance.description,
    )


def fetch_assessment_by_subject_id(subject_id: int, db: Session):
    statement = select(Assessment.id, Assessment.title).where(
        Assessment.subject_id == subject_id
    )
    assessments = db.exec(statement).all()
    return [
        AssessmentMinimal(id=assessment_id, title=assessment_title)
        for assessment_id, assessment_title in assessments
    ]


def question_create(question_data: QuestionCreate, db: Session):
    try:
        create_data = question_data.model_dump()
        options = create_data.pop("options")
        question_instance = Question(**create_data)
        db.add(question_instance)
        db.flush()
        if options:
            option_instances = [
                Options(
                    text=option.get("text"),
                    is_correct=option.get("is_correct"),
                    question_id=question_instance.id,
                )
                for option in options
            ]
            db.add_all(option_instances)
        db.commit()
        return question_instance
    except Exception as e:
        db.rollback()
        raise e


def question_update(question_id: int, update_data: QuestionUpdate, db: Session):
    try:
        question_instance = db.get(Question, question_id)
        if not question_instance:
            raise NoResultFound(f"Question with pk {question_id} not found")
        question_data = update_data.model_dump(exclude_none=True)
        options = question_data.pop("options")

        updated_instance = update_model_instance(question_instance, question_data)
        db.commit()
        if options:
            option_instances = db.exec(
                select(Options.id).where(Options.question_id == question_id)
            ).all()
            to_update_options = [
                option for option in options if option.get("id") in option_instances
            ]
            to_delete_options = [
                option for option in options if option.get("id") not in option_instances
            ]
            if to_update_options:
                option_ids = [option.get("id") for option in to_update_options]
                to_update_options = db.exec(
                    select(Options).where(Options.id.in_(option_ids))
                ).all()
                for option in to_update_options:
                    option_data = next(
                        (opt for opt in options if opt.get("id") == option.id), None
                    )
                    if option_data:
                        update_model_instance(option, option_data)
            if to_delete_options:
                option_ids = [option.get("id") for option in to_delete_options]
                db.exec(delete(Options).where(Options.id.in_(option_ids)))
        db.commit()
        print(updated_instance.question)
        return updated_instance
    except Exception as e:
        db.rollback()
        raise e


def fetch_question_by_id(question_id: int, db: Session):
    statetment = (
        select(Question, Assessment, Subject, Course)
        .join(Assessment, Question.assessment_id == Assessment.id)
        .join(Subject, Assessment.subject_id == Subject.id)
        .join(Course, Subject.course_id == Course.id)
        .options(selectinload(Question.options))
        .where(Question.id == question_id)
    )
    question, assessment, subject, course = db.exec(statetment).first()
    return QuestionFetch(
        id=question.id,
        question=question.question,
        assessment=AssessmentMinimal(id=assessment.id, title=assessment.title),
        course=BaseCourse(id=course.id, title=course.title),
        subject=BaseSubjectFetch(id=subject.id, title=subject.title),
        order=question.order,
        options=[
            OptionsFetch(id=option.id, text=option.text, is_correct=option.is_correct)
            for option in question.options
        ],
    )


def fetch_question_list(db: Session):
    statement = select(Question).options(
        joinedload(Question.assessment)
        .joinedload(Assessment.subject)
        .joinedload(Subject.course)
    )
    questions = db.exec(statement).all()
    return [
        QuestionFetch(
            id=question.id,
            question=question.question,
            order=question.order,
            assessment=AssessmentMinimal(
                id=question.assessment.id, title=question.assessment.title
            ),
            course=BaseCourse(
                id=question.assessment.subject.course.id,
                title=question.assessment.subject.course.title,
            ),
            subject=BaseSubjectFetch(
                id=question.assessment.subject.id,
                title=question.assessment.subject.title,
            ),
        )
        for question in questions
    ]
