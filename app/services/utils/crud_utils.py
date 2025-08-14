from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.db.session.session import get_db


def update_model_instance(instance: any, data: dict):
    for key, value in data.items():
        setattr(instance, key, value)
    return instance


def get_model_instance_by_id(model: any, instance_id: int):
    db = next(get_db())
    return db.get(model, instance_id)


def create_model_instance(model: any, data: dict, db: Session):
    try:
        model_instance = model(**data)
        db.add(model_instance)
        db.commit()
        db.flush(model_instance)
        return model_instance
    except IntegrityError:
        db.rollback()
        raise
