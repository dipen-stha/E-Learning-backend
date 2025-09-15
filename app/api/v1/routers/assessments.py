from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app.api.v1.schemas.assessments import AssessmentCreate, AssessmentTypeCreate
from app.db.crud.assessments import fetch_all_assessment_types, create_assessment_type
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