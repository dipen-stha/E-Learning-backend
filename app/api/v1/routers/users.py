from typing import Annotated

from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.api.v1.schemas.users import UserCreateSchema, UserFetchSchema
from app.db.crud.users import create_user, get_user_list_by_role
from app.db.session.session import get_db
from app.services.auth.permissions_mixins import IsAdmin, IsAuthenticated
from app.services.enum.users import UserRole

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

user_router = APIRouter(prefix="/users", tags=["Users"])


@user_router.post("/create/", response_model=UserFetchSchema)
def user_create(user: UserCreateSchema, db: Annotated[Session, Depends(get_db)], image: UploadFile = File(...)):
    try:
        return create_user(user, db, image)
    except IntegrityError:
        raise HTTPException(status_code=500, detail="User already exists")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@user_router.get(
    "/get/students/",
    response_model=list[UserFetchSchema],
    dependencies=[Depends(IsAuthenticated), Depends(IsAdmin)],
)
def fetch_students(db: Annotated[Session, Depends(get_db)]):
    try:
        return get_user_list_by_role(UserRole.STUDENT, db)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@user_router.get(
    "/get/tutors/",
    response_model=list[UserFetchSchema],
    dependencies=[Depends(IsAuthenticated), Depends(IsAdmin)],
)
def fetch_teachers(db: Annotated[Session, Depends(get_db)]):
    try:
        return get_user_list_by_role(UserRole.TUTOR, db)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))
