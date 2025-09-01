from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlmodel import Session

from app.api.v1.schemas.common import (
    BaseCommonUpdate,
    UserContentCreate,
    UserContentFetch,
    UserCourseCreate,
    UserCourseFetch,
    UserCourseStats,
    UserSubjectCreate,
    UserSubjectFetch,
    UserUnitCreate,
    UserUnitFetch,
)
from app.db.crud.common import (
    user_content_create,
    user_content_fetch,
    user_course_create,
    user_course_fetch,
    user_course_fetch_by_id,
    user_course_stats,
    user_course_update,
    user_subject_create,
    user_subject_fetch,
    user_subject_update,
    user_unit_create,
    user_unit_fetch,
    user_unit_update, user_subject_fetch_by_subject, fetch_user_units_by_subject,
)
from app.db.models.users import User
from app.db.session.session import get_db
from app.services.auth.core import get_current_user


common_router = APIRouter(
    prefix="/common", tags=["Commons"], dependencies=[Depends(get_current_user)]
)


@common_router.post("/user-course/create/", response_model=UserCourseFetch)
def create_user_course(
    user_course: UserCourseCreate, db: Annotated[Session, Depends(get_db)]
):
    try:
        user_course_data = user_course_create(user_course, db)
        return user_course_data
    except ValidationError as ve:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({"errors": ve.errors()}),
        )
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@common_router.get(
    "/user-course/fetch/{user_id}/", response_model=list[UserCourseFetch]
)
def fetch_user_courses(user_id: int, db: Annotated[Session, Depends(get_db)]):
    try:
        user_course_data = user_course_fetch(user_id, db)
        return user_course_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"error": f"{e}"}
        )


@common_router.get("/user-course/fetch-by-course/{course_id}/")
def fetch_user_course_by_course_id(
    course_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        return user_course_fetch_by_id(course_id, user, db)
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_type": error.__class__.__name__,
                "error_message": str(error),
            },
        )


@common_router.get(
    "/user-course/fetch-user-stats/{user_id}/", response_model=UserCourseStats
)
def fetch_user_course_stats(user_id: int, db: Annotated[Session, Depends(get_db)]):
    try:
        return user_course_stats(user_id, db)
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_type": error.__class__.__name__,
                "error_message": str(error),
            },
        )


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


@common_router.post("/user-subject/create/", response_model=UserSubjectFetch)
def create_user_subject(
    user_subject: UserSubjectCreate, db: Annotated[Session, Depends(get_db)], user: Annotated[User, Depends(get_current_user)]
):
    try:
        user_subject.user_id = user.id
        user_subject_data = user_subject_create(user_subject, db)
        return user_subject_data
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@common_router.get(
    "/user-subject/fetch/{user_id}/", response_model=list[UserSubjectFetch]
)
def fetch_user_subject(user_id: int, db: Annotated[Session, Depends(get_db)]):
    try:
        user_subject_data = user_subject_fetch(user_id, db)
        return user_subject_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@common_router.get("/user-subject/{subject_id}/status/")
def fetch_user_subject_status(subject_id: int, db: Annotated[Session, Depends(get_db)], user: Annotated[User, Depends(get_current_user)]):
    try:
        return user_subject_fetch_by_subject(subject_id, user.id, db)
    except Exception as error:
        raise HTTPException(status_code=500, detail={
            "error_type": error.__class__.__name__,
            "error_message": str(error),
        })

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
    user_unit: UserUnitCreate, db: Annotated[Session, Depends(get_db)], user: Annotated[User, Depends(get_current_user)]
):
    try:
        user_unit.user_id = user.id
        user_unit_instance = user_unit_create(user_unit, db)
        return user_unit_instance
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@common_router.get("/user-unit/fetch/{user_id}/", response_model=list[UserUnitFetch])
def fetch_user_unit(user_id: int, db: Annotated[Session, Depends(get_db)]):
    try:
        user_unit_data = user_unit_fetch(user_id, db)
        return user_unit_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@common_router.patch(
    "/user-unit/update/{user_unit_id}/", response_model=list[UserUnitFetch]
)
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


@common_router.get("/user-unit/{subject_id}/status/")
def fetch_user_units_status(subject_id: int, db: Annotated[Session, Depends(get_db)], user: Annotated[User, Depends(get_current_user)]):
    try:
        return fetch_user_units_by_subject(subject_id, user.id, db)
    except Exception as error:
        raise HTTPException(status_code=500, detail={
            "error_type": error.__class__.__name__,
            "error_message": str(error),
        })

@common_router.post("/user-content/create/", response_model=UserContentFetch)
def create_user_content(
    user_content: UserContentCreate, db: Annotated[Session, Depends(get_db)]
):
    try:
        return user_content_create(user_content, db)
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)
        )


@common_router.get(
    "/user-content/fetch/{user_id}/", response_model=list[UserContentFetch]
)
def fetch_user_content(user_id: int, db: Annotated[Session, Depends(get_db)]):
    try:
        return user_content_fetch(user_id, db)
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)
        )
