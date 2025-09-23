import json

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.params import Query
from pydantic import ValidationError
from sqlalchemy.exc import NoResultFound
from sqlmodel import Session
from starlette import status
from starlette.responses import JSONResponse

from app.api.v1.schemas.courses import (
    Base,
    BaseCourse,
    BaseSubjectFetch,
    BaseUnit,
    CategoryFetch,
    ContentCreate,
    ContentFetch,
    ContentUpdate,
    CourseCreate,
    CourseFetch,
    CourseUpdate,
    LatestCourseFetch,
    SubjectCreate,
    SubjectFetch,
    SubjectUpdate,
    UnitCreate,
    UnitFetch,
    UnitUpdate,
)
from app.api.v1.schemas.extras import FilterParams
from app.db.crud.courses import (
    content_create,
    content_update,
    course_category_create,
    course_create,
    course_fetch_by_id,
    course_update,
    fetch_all_units,
    fetch_content_by_id,
    fetch_contents,
    fetch_latest_courses,
    fetch_minimal_units,
    fetch_subjects_by_courses,
    fetch_subjects_minimal,
    fetch_unit_by_id,
    fetch_units_by_subject,
    get_all_categories,
    list_all_courses,
    list_minimal_courses,
    subject_create,
    subject_fetch_by_id,
    subject_update,
    unit_create,
    unit_update,
)
from app.db.models.users import User
from app.db.session.session import get_db
from app.services.auth.core import get_current_user


course_router = APIRouter(prefix="/courses", tags=["Courses"])


@course_router.post("/category/create/", response_model=CategoryFetch)
def create_category(data: Base, db: Annotated[Session, Depends(get_db)]):
    try:
        return course_category_create(data.title, db)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@course_router.get("/category/get/")
def get_categories(
    db: Annotated[Session, Depends(get_db)], params: Annotated[FilterParams, Query()]
):
    try:
        return get_all_categories(db, params=params)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@course_router.get("/get/latest-courses/", response_model=list[LatestCourseFetch])
def get_latest_courses(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        return fetch_latest_courses(db, user.id)
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


@course_router.get("/get/all/")
async def get_all_courses(
    db: Annotated[Session, Depends(get_db)], params: Annotated[FilterParams, Query()]
):
    try:
        return list_all_courses(db, params=params)
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


@course_router.get("/get/minimal/", response_model=list[BaseCourse])
def get_minimal_courses(db: Annotated[Session, Depends(get_db)]):
    try:
        return list_minimal_courses(db)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error_type": e.__class__.__name__,
                "error_message": str(e),
            },
        )


@course_router.post("/create/", response_model=CourseFetch)
async def create_course(
    db: Annotated[Session, Depends(get_db)],
    course: str = Form(...),
    file: UploadFile = File(None),
):
    try:
        data = json.loads(course)
        course_data = CourseCreate(**data)
        return await course_create(course_data, db, file)
    except ValidationError as error:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({"errors": error.errors()}),
        )
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@course_router.patch("/{course_id}/update/", response_model=BaseCourse)
async def update_course(
    course_id: int,
    db: Annotated[Session, Depends(get_db)],
    course: str = Form(...),
    file: UploadFile = File(None),
):
    try:
        course_data = CourseUpdate(**json.loads(course))
        return await course_update(course_id, course_data, db, file)
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


@course_router.get("/get/{course_id}/")
def get_course_by_id(course_id: int, db: Annotated[Session, Depends(get_db)]):
    try:
        return course_fetch_by_id(course_id, db)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Course not found")
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


@course_router.patch("/subject/{subject_id}/update/")
def update_subject(
    subject_id: int, subject: SubjectUpdate, db: Annotated[Session, Depends(get_db)]
):
    try:
        return subject_update(subject_id, subject, db)
    except ValidationError as e:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({"errors": e.errors()}),
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={
                "error_type": error.__class__.__name__,
                "error_message": str(error),
            },
        )


@course_router.get("/subject/get/all/", response_model=list[SubjectFetch])
def list_all_subjects(
    db: Annotated[Session, Depends(get_db)],
    params: Annotated[FilterParams, Query()] = None,
):
    try:
        return fetch_subjects_by_courses(db, params=params)
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


@course_router.get("/subject/by_course/{course_id}/", response_model=list[SubjectFetch])
def list_subjects_by_course(course_id: int, db: Annotated[Session, Depends(get_db)]):
    try:
        return fetch_subjects_by_courses(db, course_id)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@course_router.get("/subject/get_by_id/{subject_id}/")
def fetch_subject_by_id(subject_id: int, db: Annotated[Session, Depends(get_db)]):
    try:
        return subject_fetch_by_id(subject_id, db)
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


@course_router.get(
    "/subject/minimal/{course_id}", response_model=list[BaseSubjectFetch]
)
def list_subjects_minimal(course_id: int, db: Annotated[Session, Depends(get_db)]):
    try:
        return fetch_subjects_minimal(db, course_id)
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


@course_router.get("/unit/get/all/")
def list_all_units(
    db: Annotated[Session, Depends(get_db)], params: Annotated[FilterParams, Query()]
):
    try:
        return fetch_all_units(db, params=params)
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


@course_router.post("/unit/create/", response_model=UnitFetch)
def create_unit(unit: UnitCreate, db: Annotated[Session, Depends(get_db)]):
    try:
        return unit_create(unit, db)
    except ValidationError as e:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({"errors": e.errors()}),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@course_router.patch("/unit/{unit_id}/update/")
def update_unit(
    unit_id: int, unit: UnitUpdate, db: Annotated[Session, Depends(get_db)]
):
    try:
        return unit_update(unit_id, unit, db)
    except ValidationError as e:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({"errors": e.errors()}),
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={
                "error_type": error.__class__.__name__,
                "error_message": str(error),
            },
        )


@course_router.get("/unit/get_by_subject/{subject_id}/", response_model=list[UnitFetch])
def get_units_by_subject(subject_id: int, db: Annotated[Session, Depends(get_db)]):
    try:
        return fetch_units_by_subject(subject_id, db)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@course_router.get("/unit/minimal/", response_model=list[BaseUnit])
def minimal_units(db: Annotated[Session, Depends(get_db)]):
    try:
        return fetch_minimal_units(db)
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


@course_router.get("/unit/{unit_id}/")
def get_unit_by_id(unit_id: int, db: Annotated[Session, Depends(get_db)]):
    try:
        return fetch_unit_by_id(unit_id, db)
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


@course_router.get(
    "/unit/minimal/by_subject/{subject_id}/", response_model=list[BaseUnit]
)
def minimal_units_by_subject(subject_id: int, db: Annotated[Session, Depends(get_db)]):
    try:
        return fetch_minimal_units(db, subject_id)
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


@course_router.post("/content/create/")
async def create_content(
    db: Annotated[Session, Depends(get_db)],
    content: str = Form(...),
    file: UploadFile = File(None),
):
    try:
        data = json.loads(content)
        video_time_stamps = data.pop("video_time_stamps")
        if video_time_stamps:
            for item in video_time_stamps:
                stamp = item.pop("time_stamp")
                if stamp is None:
                    continue
                minutes, seconds = stamp.split(":")
                item["time_stamp"] = (int(minutes) * 60) + int(seconds)
            data["video_time_stamps"] = video_time_stamps
        content_data = ContentCreate(**data)
        content = await content_create(content_data, db, file)
        return content
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


@course_router.patch("/content/{content_id}/update/", response_model=ContentFetch)
async def update_content(
    content_id: int,
    db: Annotated[Session, Depends(get_db)],
    content: str = Form(...),
    file: UploadFile = File(None),
):
    try:
        data = json.loads(content)
        content_data = ContentUpdate(**data)
        return await content_update(content_id, content_data, db, file)
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


@course_router.get("/content/fetch/all/")
def fetch_all_contents(
    db: Annotated[Session, Depends(get_db)], params: Annotated[FilterParams, Query()]
):
    try:
        return fetch_contents(db, params=params)
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


@course_router.get("/content/get/{content_id}/")
def get_content_by_id(content_id: int, db: Annotated[Session, Depends(get_db)]):
    try:
        return fetch_content_by_id(content_id, db)
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
