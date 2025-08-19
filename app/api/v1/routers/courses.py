import json
from typing import Annotated

from pydantic import ValidationError
from sqlmodel import Session

from app.api.v1.schemas.courses import (
    Base,
    BaseCourse,
    CategoryFetch,
    ContentCreate,
    ContentFetch,
    ContentUpdate,
    CourseCreate,
    CourseFetch,
    SubjectCreate,
    SubjectFetch,
    UnitContentCreate,
    UnitContentFetch,
    UnitContentUpdate,
    UnitCreate,
    UnitFetch,
    UnitUpdate,
)
from app.db.crud.courses import (
    content_create,
    content_update,
    course_category_create,
    course_create,
    course_fetch_by_id,
    course_update,
    fetch_by_content_unit,
    fetch_by_course,
    fetch_units_by_subject,
    list_all_courses,
    subject_create,
    unit_content_create,
    unit_content_update,
    unit_create,
    unit_update, get_all_categories,
)
from app.db.session.session import get_db

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Form

course_router = APIRouter(prefix="/courses", tags=["Courses"])


@course_router.post("/category/create/", response_model=CategoryFetch)
def create_category(data: Base, db: Annotated[Session, Depends(get_db)]):
    try:
        return course_category_create(data.title, db)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@course_router.get("/category/get/", response_model=list[CategoryFetch])
def get_categories(db: Session = Depends(get_db)):
    try:
        return get_all_categories(db)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))

@course_router.get("/get/all/", response_model=list[CourseFetch])
def get_all_courses(db: Annotated[Session, Depends(get_db)]):
    try:
        return list_all_courses(db)
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={
                "error_type": error.__class__.__name__,
                "error_message": str(error),
            },
        )


@course_router.post("/create/", response_model=CourseFetch)
def create_course(
    db: Annotated[Session, Depends(get_db)],
    course: str = Form(...),
    file: UploadFile = File(None),
):
    try:
        data = json.loads(course)
        data["category_id"] = int(data.get("category_id"))
        data["instructor_id"] = int(data.get("instructor_id"))
        course_data = CourseCreate(**data)
        return course_create(course_data, db, file)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@course_router.patch("/update/{course_id}/", response_model=BaseCourse)
async def update_course(
    course_id: int,
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile = File(...),
):
    try:
        return await course_update(course_id, db, file)
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={
                "error_type": error.__class__.__name__,
                "error_message": str(error),
            },
        )


@course_router.get("/get/{course_id}/")
def get_course_by_id(course_id: int, db: Annotated[Session, Depends(get_db)]):
    try:
        return course_fetch_by_id(course_id, db)
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={
                "error_type": error.__class__.__name__,
                "error_message": str(error),
            },
        )


@course_router.post("/subject/create/", response_model=SubjectFetch)
def create_subject(subject: SubjectCreate, db: Annotated[Session, Depends(get_db)]):
    try:
        return subject_create(subject, db)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@course_router.get("/subject/by_course/{course_id}/", response_model=list[SubjectFetch])
def list_subjects_by_course(course_id: int, db: Annotated[Session, Depends(get_db)]):
    try:
        return fetch_by_course(course_id, db)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@course_router.post("/unit/create/", response_model=UnitFetch)
def create_unit(unit: UnitCreate, db: Annotated[Session, Depends(get_db)]):
    try:
        return unit_create(unit, db)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@course_router.patch("/unit/update/{unit_id}/", response_model=UnitFetch)
def update_unit(
    unit_id: int, unit: UnitUpdate, db: Annotated[Session, Depends(get_db)]
):
    try:
        return unit_update(unit_id, unit, db)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@course_router.get("/unit/get_by_subject/{subject_id}/", response_model=list[UnitFetch])
def get_units_by_subject(subject_id: int, db: Annotated[Session, Depends(get_db)]):
    try:
        return fetch_units_by_subject(subject_id, db)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@course_router.post("/unit-content/create/", response_model=UnitContentFetch)
def create_unit_content(
    unit_content: UnitContentCreate, db: Annotated[Session, Depends(get_db)]
):
    try:
        return unit_content_create(unit_content, db)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@course_router.patch(
    "/unit-content/update/{content_id}/", response_model=UnitContentFetch
)
def update_unit_fetch(
    content_id: int,
    unit_content: UnitContentUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return unit_content_update(content_id, unit_content, db)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@course_router.post("/content/create/", response_model=ContentFetch)
def create_content(content: ContentCreate, db: Annotated[Session, Depends(get_db)]):
    try:
        return content_create(content, db)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@course_router.patch("/content/update/{content_id}/", response_model=ContentFetch)
def update_content(
    content_id: int, content: ContentUpdate, db: Annotated[Session, Depends(get_db)]
):
    try:
        return content_update(content_id, content, db)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@course_router.get(
    "/content/list/get_by_unit_content/{unit_content_id}/",
    response_model=list[ContentFetch],
)
def get_contents_by_unit_content(
    content_id: int, db: Annotated[Session, Depends(get_db)]
):
    try:
        return fetch_by_content_unit(content_id, db)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))
