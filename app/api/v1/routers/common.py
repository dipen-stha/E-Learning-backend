from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError

from sqlmodel import Session
from sqlalchemy.exc import IntegrityError

from app.db.session.session import get_db
from app.api.v1.schemas.common import (
    UserUnitCreate,
    UserContentCreate,
    UserCourseCreate,
    UserSubjectCreate,
    BaseCommonUpdate,
    UserCourseFetch,
)
from app.db.crud.common import (
    user_course_create,
    user_course_update,
    user_subject_create,
    user_subject_update,
    user_unit_create,
    user_unit_update,
)

common_router = APIRouter(prefix="/common", tags=["Commons"])


@common_router.post("/user-course/create/", response_model=UserCourseFetch)
def create_user_course(
    user_course: UserCourseCreate, db: Annotated[Session, Depends(get_db)]
):
    try:
        user_course_data = user_course_create(user_course, db)
        return user_course_data
    except ValidationError as ve:
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=jsonable_encoder({"errors": ve.errors()}))
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@common_router.patch("/user-course/update/update/{user_course_id}/")
def update_user_course(
    user_course_id: int,
    user_course: BaseCommonUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        user_course_data = user_course_update(user_course_id, user_course, db)
        return user_course_data
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@common_router.post("/user-subject/create/")
def create_user_subject(
    user_subject: UserSubjectCreate, db: Annotated[Session, Depends(get_db)]
):
    try:
        user_subject_data = user_subject_create(user_subject, db)
        return user_subject_data
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@common_router.patch("/user-subject/update/{user_subject_id}/")
def update_user_subject(
    user_subject_id: int,
    user_subject: BaseCommonUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        user_subject_instance = user_subject_update(user_subject_id, user_subject, db)
        return user_subject_instance
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@common_router.post("/user-unit/create/")
def create_user_unit(
    user_unit: UserUnitCreate, db: Annotated[Session, Depends(get_db)]
):
    try:
        user_unit_instance = user_unit_create(user_unit, db)
        return user_unit_instance
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@common_router.patch("/user-unit/update/{user_unit_id}/")
def update_user_unit(
    user_unit_id: int,
    user_unit: BaseCommonUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        user_unit_instance = user_unit_update(user_unit_id, user_unit, db)
        return user_unit_instance
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))
