from sqlalchemy.exc import NoResultFound, InvalidRequestError
from sqlalchemy.orm import joinedload, selectinload
from sqlmodel import Session, select

from app.api.v1.schemas.assessments import AssessmentTypeCreate, AssessmentTypeUpdate, AssessmentTypeFetch, \
    AssessmentCreate, AssessmentUpdate, AssessmentsFetch
from app.api.v1.schemas.courses import BaseSubjectFetch
from app.db.models.assessments import AssessmentType, Assessment
from app.db.models.courses import Subject
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

def update_assessment_type(assessment_type_id: int, assessment_type: AssessmentTypeUpdate, db: Session):
    try:
        assessment_instance = db.get(assessment_type_id, AssessmentType)
        if not assessment_instance:
            raise NoResultFound(f"Assessment with pk {assessment_type_id} not found")
        subject_id = assessment_type.subject_id
        if not db.get(subject_id, Subject):
            raise NoResultFound(f"Subject with pk {subject_id} not found")
        assessment_data = assessment_type.model_dump()
        updated_assessment_instance = update_model_instance(assessment_instance, assessment_data)
        db.add(updated_assessment_instance)
        db.commit()
        db.refresh(updated_assessment_instance)
        return updated_assessment_instance
    except Exception as e:
        db.rollback()
        raise e

def fetch_all_assessment_types(db: Session):
    try:
        statement = (
            select(AssessmentType)
        )
        all_assessment_type = db.exec(statement).all()
        return [AssessmentTypeFetch(
            id=assessment_type.id,
            title=assessment_type.title,
            icon=assessment_type.icon,
            description=assessment_type.description
        ) for assessment_type in all_assessment_type]
    except Exception as e:
        raise e

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
        assessment_instance = db.get(assessment_id, Assessment)
        if not assessment_instance:
            raise NoResultFound(f"Assessment with pk {assessment_id} not found")
        subject_id = assessment.subject_id
        order = assessment.order
        existing_order_assessment = db.exec(select(Assessment).where(Assessment.subject_id == subject_id, Assessment.order == order, Assessment.id != assessment_id)).all()
        if existing_order_assessment:
            raise InvalidRequestError(f"Assessment with order {order} already exists")
        assessment_data = assessment.model_dump()
        updated_assessment_instance = update_model_instance(assessment_instance, assessment_data)
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
            .options(joinedload(Assessment.assessment_type), joinedload(Assessment.subject), selectinload(Assessment.questions))
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
                    icon=assessment.assessment_type.icon
                ),
                max_points=assessment.max_points,
                pass_points=assessment.pass_points,
                subject=BaseSubjectFetch(id=assessment.subject.id, title=assessment.subject.title),
                order=assessment.order,
                description=assessment.description
            )
            for assessment in assessment_instances
        ]
    except Exception as e:
        raise e


