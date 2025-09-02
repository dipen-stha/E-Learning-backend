import json

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session
from starlette.responses import JSONResponse

from app.api.v1.schemas.users import (
    MinimalUserFetch,
    StudentFetchSchema,
    UserCreateSchema,
    UserFetchSchema,
    UserUpdateSchema,
)
from app.db.crud.users import (
    create_user,
    fetch_user_by_id,
    get_minimal_user_list,
    get_students_list,
    get_user_list_by_role,
    get_user_stats,
    update_user,
)
from app.db.session.session import get_db
from app.services.auth.permissions_mixins import IsAdmin, IsAuthenticated
from app.services.enum.users import UserRole


user_router = APIRouter(
    prefix="/users", tags=["Users"], dependencies=[Depends(IsAdmin)]
)


@user_router.post("/create/", response_model=UserFetchSchema)
async def user_create(
    db: Annotated[Session, Depends(get_db)],
    user: str = Form(...),
    file: UploadFile = File(None),
):
    try:
        user_data = UserCreateSchema(**json.loads(user))
        return await create_user(user_data, db, file)
    except IntegrityError:
        raise HTTPException(status_code=500, detail="User already exists")
    except ValidationError as ve:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({"errors": ve.errors()}),
        )
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@user_router.patch("/{user_id}/update/")
async def user_update(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: str = Form(...),
    file: UploadFile = File(None),
):
    try:
        user_data = UserUpdateSchema(**json.loads(user))
        return await update_user(user_id, user_data, db, file)
    except IntegrityError:
        raise HTTPException(status_code=500, detail="User already exists")
    except ValidationError as ve:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({"errors": ve.errors()}),
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={
                "error_type": error.__class__.__name__,
                "error_message": str(error),
            },
        )


@user_router.get("/{user_id}/")
async def get_user_by_id(user_id: int, db: Annotated[Session, Depends(get_db)]):
    try:
        return fetch_user_by_id(user_id, db)
    except ValidationError as ve:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({"errors": ve.errors()}),
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={
                "error_type": error.__class__.__name__,
                "error_message": str(error),
            },
        )


@user_router.get(
    "/get/students/",
    response_model=list[StudentFetchSchema],
)
def fetch_students(db: Annotated[Session, Depends(get_db)]):
    try:
        return get_students_list(db)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))
    # return get_students_list(db)


@user_router.get(
    "/tutors/get/",
    response_model=list[UserFetchSchema],
    dependencies=[Depends(IsAuthenticated), Depends(IsAdmin)],
)
def fetch_teachers(db: Annotated[Session, Depends(get_db)]):
    try:
        return get_user_list_by_role(UserRole.TUTOR, db)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@user_router.get(
    "/tutors/get/minimal/",
    response_model=list[MinimalUserFetch],
)
def fetch_minimal_tutors_list(db: Annotated[Session, Depends(get_db)]):
    try:
        return get_minimal_user_list(db)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@user_router.get("/students/get/user-stats/")
def user_stats(db: Annotated[Session, Depends(get_db)]):
    try:
        return get_user_stats(UserRole.STUDENT, db)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))
