from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import selectinload
from sqlmodel import select, Session

from app.api.v1.schemas.courses import (
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
from app.db.models.courses import (
    Category,
    CategoryCourseLink,
    Contents,
    Course,
    Subject,
    Unit,
    UnitContents,
)
from app.services.utils.crud_utils import update_model_instance


def course_category_create(title: str, db: Session) -> CategoryFetch:
    category_instance = Category(title=title)
    db.add(category_instance)
    db.commit()
    db.refresh(category_instance)
    return CategoryFetch.model_validate(category_instance)


def list_all_courses(db: Session) -> list[CourseFetch]:
    courses = db.exec(select(Course).options(selectinload(Course.categories)))
    courses_data = [CourseFetch.from_orm(course) for course in courses]
    return courses_data


def course_create(course: CourseCreate, db: Session) -> CourseFetch:
    data = course.model_dump()
    categories_id = data.pop("categories_id")
    categories = db.exec(select(Category.id).where(Category.id.in_(categories_id)))
    course = Course(**data)
    db.add(course)
    db.flush()
    course_categories_link = [
        CategoryCourseLink(course_id=course.id, category_id=category)
        for category in categories
    ]
    db.add_all(course_categories_link)
    db.commit()
    db.refresh(course)
    return CourseFetch.from_orm(course)


def subject_create(subject: SubjectCreate, db: Session) -> SubjectFetch:
    data = subject.model_dump()
    course_id = data.get("course_id")
    course = db.exec(select(Course).where(Course.id == course_id)).first()
    if not course:
        raise NoResultFound(f"No course with id {course_id}")
    subject_instance = Subject(**data)
    db.add(subject_instance)
    db.commit()
    db.refresh(subject_instance)
    return SubjectFetch.from_orm(subject_instance)


def fetch_by_course(course_id: int, db: Session) -> list[SubjectFetch]:
    subjects = db.exec(
        select(Subject)
        .options(selectinload(Subject.course))
        .where(Subject.course_id == course_id)
    )
    subjects_data = [SubjectFetch.from_orm(subject) for subject in subjects]
    return subjects_data


def unit_create(unit: UnitCreate, db: Session) -> UnitFetch:
    data = unit.model_dump()
    subject_id = data.get("subject_id")
    subject = db.get(Subject, subject_id)
    if not subject:
        raise NoResultFound(f"No subject with id {subject_id}")
    unit_instance = Unit(**data)
    db.add(unit_instance)
    db.commit()
    db.refresh(unit_instance)
    return UnitFetch.from_orm(unit_instance)


def unit_update(unit_id: int, unit: UnitUpdate, db: Session) -> UnitFetch:
    data = unit.model_dump()
    unit_instance = db.exec(select(Unit).where(Unit.id == unit_id)).first()
    if not unit_instance:
        raise NoResultFound(f"No unit with id {unit_id}")
    if data.get("subject_id"):
        subject = db.get(Subject, data["subject_id"])
        if not subject:
            raise NoResultFound(f"No subject with id {unit_id}")
    updated_unit_instance = update_model_instance(unit_instance, data)
    db.add(updated_unit_instance)
    db.commit()
    db.refresh(updated_unit_instance)
    return UnitFetch.from_orm(updated_unit_instance)


def fetch_units_by_subject(subject_id: int, db: Session) -> list[UnitFetch]:
    units = db.exec(
        select(Unit)
        .options(selectinload(Unit.subject))
        .where(Unit.subject_id == subject_id)
    )
    return [UnitFetch.from_orm(unit) for unit in units]


def unit_content_create(
    unit_content: UnitContentCreate, db: Session
) -> UnitContentFetch:
    data = unit_content.model_dump()
    unit_instance = db.get(Unit, data.get("unit_id"))
    if not unit_instance:
        raise NoResultFound(f"No unit with id {data.get('unit_id')}")
    unit_content_instance = UnitContents(**data)
    db.add(unit_content_instance)
    db.commit()
    db.refresh(unit_content_instance)
    return UnitContentFetch.from_orm(unit_content_instance)


def unit_content_update(
    unit_content_id: int, unit_content: UnitContentUpdate, db: Session
) -> UnitContentFetch:
    data = unit_content.model_dump()
    unit_id = unit_content.get("unit_id")
    if unit_id:
        unit_instance = db.get(Unit, data.get("unit_id"))
        if not unit_instance:
            raise NoResultFound(f"No unit with id {data.get('unit_id')}")
    updated_data = {key: value for key, value in data.items() if value is not None}
    unit_content = db.get(UnitContents, unit_content_id)
    if not unit_content:
        raise NoResultFound(f"No unit content with id {unit_content_id}")
    updated_instance = update_model_instance(unit_content, updated_data)
    db.add(updated_instance)
    db.commit()
    db.refresh(updated_instance)
    return UnitContentFetch.from_orm(updated_instance)


def content_create(content: ContentCreate, db: Session) -> ContentFetch:
    data = content.model_dump()
    unit_id = data.get("unit_id")
    unit_instance = db.get(Unit, unit_id)
    if not unit_instance:
        raise NoResultFound(f"No unit with id {unit_id}")
    content_instance = Contents(**data)
    db.add(content_instance)
    db.commit()
    db.refresh(content_instance)
    return ContentFetch.from_orm(content_instance)


def content_update(
    content_id: int, content: ContentUpdate, db: Session
) -> ContentFetch:
    data = content.model_dump()
    unit_id = data.get("unit_id")
    content_instance = db.get(Contents, content_id)
    if unit_id:
        unit_instance = db.get(Unit, unit_id)
        if not unit_instance:
            raise NoResultFound(f"No unit with id {unit_id}")
    updated_instance = update_model_instance(content_instance, data)
    db.add(updated_instance)
    db.commit()
    db.refresh(updated_instance)
    return ContentFetch.from_orm(updated_instance)


def fetch_by_content_unit(content_unit_id: int, db: Session) -> list[ContentFetch]:
    content_unit = db.get(UnitContents, content_unit_id)
    if not content_unit:
        raise NoResultFound(f"No content unit with id {content_unit_id}")
    content_units = db.exec(
        select(Contents)
        .options(selectinload(Contents.unit_content))
        .where(Contents.content_unit_id == content_unit_id)
    )
    return [ContentFetch.from_orm(content_unit) for content_unit in content_units]
