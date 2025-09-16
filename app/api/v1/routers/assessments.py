from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app.api.v1.schemas.assessments import AssessmentCreate, AssessmentTypeCreate, AssessmentUpdate
from app.db.crud.assessments import fetch_all_assessment_types, create_assessment_type, fetch_all_assessments, \
    assessment_by_id, update_assessment, create_assessment, fetch_assessment_type_by_id
from app.db.session.session import get_db

assessments_router = APIRouter(prefix="/assessments", tags=["Assessments"])

@assessments_router.get("/type/all/")
def list_all_assessment_types(db: Annotated[Session, Depends(get_db)]):
    try:
        return fetch_all_assessment_types(db)
    except ValidationError as error:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({"errors": error.errors()}),
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={
                "error_type": error.__class__.__name__,
                "error_message": str(error),
            },
        )


@assessments_router.get("/type/get/{type_id}/")
def get_assessment_by_id(type_id: int, db: Annotated[Session, Depends(get_db)]):
    try:
        return fetch_assessment_type_by_id(type_id, db)
    except ValidationError as error:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({"errors": error.errors()}),
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={
                "error_type": error.__class__.__name__,
                "error_message": str(error),
            },
        )

@assessments_router.post("/type/create/")
def create_new_assessment(assessment_type: AssessmentTypeCreate, db: Session = Depends(get_db)):
    try:
        return create_assessment_type(assessment_type, db)
    except ValidationError as error:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({"errors": error.errors()}),
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={
                "error_type": error.__class__.__name__,
                "error_message": str(error),
            },
        )

@assessments_router.get("/all/")
def list_assessments(db: Annotated[Session, Depends(get_db)]):
    try:
        return fetch_all_assessments(db)
    except ValidationError as error:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({"errors": error.errors()}),
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={
                "error_type": error.__class__.__name__,
                "error_message": str(error),
            },
        )


@assessments_router.post("/create/")
def create_new_assessment(assessment: AssessmentCreate, db: Annotated[Session, Depends(get_db)]):
    try:
        return create_assessment(assessment, db)
    except ValidationError as error:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({"errors": error.errors()}),
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={
                "error_type": error.__class__.__name__,
                "error_message": str(error),
            },
        )


@assessments_router.get("/{assessment_id}/get/")
def fetch_assessment_by_id(assessment_id: int, db: Annotated[Session, Depends(get_db)]):
    try:
        return assessment_by_id(assessment_id, db)
    except ValidationError as error:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({"errors": error.errors()}),
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={
                "error_type": error.__class__.__name__,
                "error_message": str(error),
            },
        )

@assessments_router.patch("/{assessment_id}/update/")
def assessment_update(assessment_id: int, assessment: AssessmentUpdate, db: Annotated[Session, Depends(get_db)]):
    try:
        return update_assessment(assessment_id, assessment, db)
    except ValidationError as error:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({"errors": error.errors()}),
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={
                "error_type": error.__class__.__name__,
                "error_message": str(error),
            },
        )