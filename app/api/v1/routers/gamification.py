from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.encoders import jsonable_encoder

from pydantic import ValidationError

from sqlmodel import select, Session
from starlette.responses import JSONResponse

from app.api.v1.schemas.gamification import StreakTypeCreate, StreakTypeUpdate
from app.db.crud.gamification import create_or_update_user_streak, create_streak_type, update_streak_type, \
    remove_streak_type, fetch_streak_type_by_id, fetch_all_streak_types
from app.db.models.users import User
from app.db.session.session import get_db
from app.services.auth.core import get_current_user

gamification_router = APIRouter(prefix="/gamification", tags=["Gamification"])

@gamification_router.get("/streak-type/all/")
def get_streak_type(db: Annotated[Session, Depends(get_db)]):
    try:
        return fetch_all_streak_types(db)
    except ValidationError as error:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({"errors": error.errors()}),
        )

    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail={
            "error_type": error.__class__.__name__,
            "error_message": str(error)
        })

@gamification_router.post("/streak-type/create/")
def streak_type_create(streak_type: StreakTypeCreate, db: Annotated[Session, Depends(get_db)]):
    try:
        return create_streak_type(streak_type, db)
    except ValidationError as error:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({"errors": error.errors()}),
        )

    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={
            "error_type": error.__class__.__name__,
            "error_message": str(error)
        })


@gamification_router.patch("/streak-type/{streak_type_id}/update/")
def streak_type_update(streak_type_id: int, streak_type: StreakTypeUpdate, db: Annotated[Session, Depends(get_db)]):
    try:
        return update_streak_type(streak_type_id, streak_type, db)
    except ValidationError as error:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({"errors": error.errors()}),
        )
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={
            "error_type": error.__class__.__name__,
            "error_message": str(error)
        })


@gamification_router.delete("/streak-type/delete/{streak_type_id}/")
def streak_type_delete(streak_type_id: int, db: Session = Depends(get_db)):
    try:
        return remove_streak_type(streak_type_id, db)
    except ValidationError as error:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({"errors": error.errors()}),
        )
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={
            "error_type": error.__class__.__name__,
            "error_message": str(error)
        })


@gamification_router.get("/streak-type/get/{streak_type_id}/")
def streak_type_by_id(streak_type_id: int, db: Annotated[Session, Depends(get_db)]):
    try:
        return fetch_streak_type_by_id(streak_type_id, db)
    except ValidationError as error:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({"errors": error.errors()}),
        )
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={
            "error_type": error.__class__.__name__,
            "error_message": str(error)
        })


@gamification_router.post("/user-streak/create-update/")
def user_streak_create_update(streak_type_id: int, db: Annotated[Session, Depends(get_db)], user: Annotated[User, Depends(get_current_user)]):
    try:
        return create_or_update_user_streak(user.id, streak_type_id, db)
    except ValidationError as error:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({"errors": error.errors()}),
        )

    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={
            "error_type": error.__class__.__name__,
            "error_message": str(error)
        })