import json

from typing import Annotated

from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.api.v1.schemas.users import UserCreateSchema, UserFetchSchema, StudentFetchSchema, MinimalUserFetch
from app.db.crud.users import create_user, get_user_list_by_role, get_students_list, get_minimal_user_list, \
    get_user_stats
from app.db.session.session import get_db
from app.services.auth.permissions_mixins import IsAdmin, IsAuthenticated
from app.services.enum.users import UserRole

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Form

user_router = APIRouter(prefix="/users", tags=["Users"])


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
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@user_router.get(
    "/get/students/",
    response_model=list[StudentFetchSchema],
    # dependencies=[Depends(IsAuthenticated), Depends(IsAdmin)],
)
def fetch_students(db: Annotated[Session, Depends(get_db)]):
    # try:
    #     return get_students_list(db)
    # except Exception as error:
    #     raise HTTPException(status_code=500, detail=str(error))
        return get_students_list(db)


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


@user_router.get(
    "/students/get/user-stats/"
)
def user_stats(db: Annotated[Session, Depends(get_db)]):
    try:
        return get_user_stats(UserRole.STUDENT, db)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))