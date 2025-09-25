from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from sqlmodel import Session
from starlette.responses import JSONResponse

from app.api.v1.schemas.gamification import (
    AchievementCreate,
    AchievementUpdate,
    StreakTypeCreate,
    StreakTypeUpdate,
)
from app.db.crud.gamification import (
    check_and_create_user_achievements,
    create_achievement_type,
    create_or_update_user_streak,
    create_streak_type,
    fetch_achievement_by_id,
    fetch_all_achievements,
    fetch_all_streak_types,
    fetch_all_user_achievements,
    fetch_streak_type_by_id,
    remove_streak_type,
    update_achievement_type,
    update_streak_type,
)
from app.db.models.users import User
from app.db.session.session import get_db
from app.services.auth.core import get_current_user
from app.services.enum.extras import AchievementRuleSet


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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_type": error.__class__.__name__,
                "error_message": str(error),
            },
        )


@gamification_router.post("/streak-type/create/")
def streak_type_create(
    streak_type: StreakTypeCreate, db: Annotated[Session, Depends(get_db)]
):
    try:
        return create_streak_type(streak_type, db)
    except ValidationError as error:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({"errors": error.errors()}),
        )

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_type": error.__class__.__name__,
                "error_message": str(error),
            },
        )


@gamification_router.patch("/streak-type/{streak_type_id}/update/")
def streak_type_update(
    streak_type_id: int,
    streak_type: StreakTypeUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return update_streak_type(streak_type_id, streak_type, db)
    except ValidationError as error:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({"errors": error.errors()}),
        )
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_type": error.__class__.__name__,
                "error_message": str(error),
            },
        )


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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_type": error.__class__.__name__,
                "error_message": str(error),
            },
        )


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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_type": error.__class__.__name__,
                "error_message": str(error),
            },
        )


@gamification_router.post("/user-streak/create-update/")
def user_streak_create_update(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        return create_or_update_user_streak(user.id, db)
    except ValidationError as error:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({"errors": error.errors()}),
        )

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_type": error.__class__.__name__,
                "error_message": str(error),
            },
        )


@gamification_router.get("/achievements/all")
def list_all_achievements(db: Annotated[Session, Depends(get_db)]):
    try:
        return fetch_all_achievements(db)
    except ValidationError as error:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({"errors": error.errors()}),
        )

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_type": error.__class__.__name__,
                "error_message": str(error),
            },
        )


@gamification_router.get("/achievements/get/{achievement_id}")
def achievement_by_id(achievement_id: int, db: Annotated[Session, Depends(get_db)]):
    try:
        return fetch_achievement_by_id(achievement_id, db)
    except ValidationError as error:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({"errors": error.errors()}),
        )

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_type": error.__class__.__name__,
                "error_message": str(error),
            },
        )


@gamification_router.post("/achievements/create/")
def achievement_create(
    achievement: AchievementCreate, db: Annotated[Session, Depends(get_db)]
):
    try:
        return create_achievement_type(achievement, db)
    except ValidationError as error:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({"errors": error.errors()}),
        )

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_type": error.__class__.__name__,
                "error_message": str(error),
            },
        )


@gamification_router.patch("/achievements/{achievement_id}/update/")
def update_achievement(
    achievement_id: int,
    achievement: AchievementUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        update_achievement_type(achievement_id, achievement, db)
    except ValidationError as error:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({"errors": error.errors()}),
        )

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_type": error.__class__.__name__,
                "error_message": str(error),
            },
        )


@gamification_router.get("/all-user-achievements/")
def fetch_user_achievements(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        return fetch_all_user_achievements(user.id, db)
    except ValidationError as error:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({"errors": error.errors()}),
        )

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_type": error.__class__.__name__,
                "error_message": str(error),
            },
        )


@gamification_router.post("/user-achievements/check-create/")
def user_achievements_create_or_update(
    rule_type: AchievementRuleSet,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        return check_and_create_user_achievements(rule_type, user.id, db)
    except ValidationError as error:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({"errors": error.errors()}),
        )

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_type": error.__class__.__name__,
                "error_message": str(error),
            },
        )
