from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import selectinload
from sqlmodel import func, select, Session

from app.api.v1.schemas.courses import (
    BaseCourse,
    CategoryFetch,
    ContentCreate,
    ContentFetch,
    ContentUpdate,
    CourseCreate,
    CourseDetailFetch,
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
from app.api.v1.schemas.users import ProfileSchema
from app.db.models.common import UserCourse
from app.db.models.courses import (
    Category,
    CategoryCourseLink,
    Contents,
    Course,
    CourseRating,
    Subject,
    Unit,
    UnitContents,
)
from app.db.models.users import User
from app.services.utils.crud_utils import update_model_instance
from app.services.utils.files import format_file_path, image_save

from fastapi import UploadFile


def course_category_create(title: str, db: Session) -> CategoryFetch:
    category_instance = Category(title=title)
    db.add(category_instance)
    db.commit()
    db.refresh(category_instance)
    return CategoryFetch.model_validate(category_instance)


def get_all_categories(db: Session) -> list[CategoryFetch]:
    categories = db.exec(select(Category)).all()
    return [CategoryFetch.model_validate(category) for category in categories]


def list_all_courses(db: Session) -> list[CourseFetch]:
    student_count_expr = func.count(User.id).label("student_count")
    rating_calculate_expr = func.avg(CourseRating.rating)
    courses = db.exec(
        select(Course, student_count_expr, rating_calculate_expr)
        .select_from(Course)
        .join(UserCourse, UserCourse.course_id == Course.id, isouter=True)
        .join(User, User.id == UserCourse.user_id, isouter=True)
        .join(CourseRating, CourseRating.course_id == Course.id, isouter=True)
        .options(
            selectinload(Course.categories),
            selectinload(Course.instructor).selectinload(User.profile),
        )
        .group_by(Course)
        .order_by(student_count_expr.desc())
    ).all()

    courses_data = [
        CourseDetailFetch(
            id=course.id,
            title=course.title,
            price=course.price,
            completion_time=course.completion_time,
            student_count=student_count,
            course_rating=course_rating,
            instructor=(
                ProfileSchema(
                    name=course.instructor.profile.name,
                    dob=course.instructor.profile.dob,
                    gender=course.instructor.profile.gender,
                    avatar=format_file_path(course.instructor.profile.avatar)
                )
            ),
            categories=[category.title for category in course.categories],
            image_url=format_file_path(course.image_url),
        )
        for course, student_count, course_rating in courses
    ]
    return courses_data


def course_create(course: CourseCreate, db: Session, file: UploadFile) -> CourseFetch:
    data = course.model_dump()
    if file:
        image_path = image_save(file)
        data["image_url"] = image_path
    categories_id = data.pop("categories_id")
    statement = select(Category.id).where(Category.id.in_(categories_id))
    categories = db.exec(statement).all()
    course_instance = Course(**data)
    db.add(course_instance)
    db.flush()
    if categories:
        course_categories_link = [
            CategoryCourseLink(course_id=course.id, category_id=category)
            for category in categories
        ]
        db.add_all(course_categories_link)
    db.commit()
    db.refresh(course_instance)
    return CourseFetch(
        id=course_instance.id,
        title=course_instance.title,
        price=course_instance.price,
        completion_time=course_instance.completion_time,
        # instructor=course_instance.instructor,
        image_url=course_instance.image_url,
    )


async def course_update(course_id: int, db: Session, file: UploadFile) -> BaseCourse:
    data = {}
    image_path = await image_save(file)
    data["image_url"] = str(image_path)
    course_instance = db.get(Course, course_id)
    if not course_instance:
        raise NoResultFound("Course not found")
    updated_course_instance = update_model_instance(course_instance, data)
    db.add(updated_course_instance)
    db.commit()
    db.refresh(updated_course_instance)
    return BaseCourse(
        id=updated_course_instance.id,
        title=updated_course_instance.title,
    )


def course_fetch_by_id(course_id: int, db: Session):
    statement = (
        select(
            Course,
            func.count(UserCourse.user_id).label("student_count"),
            func.avg(CourseRating.rating).label("course_rating"),
        )
        .join(UserCourse, UserCourse.course_id == Course.id, isouter=True)
        .join(CourseRating, CourseRating.course_id == Course.id, isouter=True)
        .options(
            selectinload(Course.categories),
            selectinload(Course.instructor).joinedload(User.profile),
            selectinload(Course.subjects).selectinload(Subject.units),
        )
        .where(Course.id == course_id)
        .group_by(Course)
    )
    course, student_count, course_rating = db.exec(statement).first()
    return CourseDetailFetch(
        id=course.id,
        title=course.title,
        description=course.description,
        completion_time=course.completion_time,
        price=course.price,
        instructor=(
            ProfileSchema(
                name=course.instructor.profile.name,
                dob=course.instructor.profile.dob,
                gender=course.instructor.profile.gender,
                avatar=format_file_path(course.instructor.profile.avatar)
            )
        ),
        course_rating=course_rating,
        student_count=student_count,
        categories=[category.title for category in course.categories],
        image_url=format_file_path(course.image_url),
        subjects=[
            SubjectFetch(
                id=subject.id,
                title=subject.title,
                completion_time=subject.completion_time,
                order=subject.order,
                units=[unit.title for unit in subject.units],
            )
            for subject in course.subjects
        ],
    )


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
    return ContentFetch(
        id=content_instance.id,
        title=content_instance.title,
        description=content_instance.description,
        content_type=content_instance.content_type,
        file_url=content_instance.file_url,
        completion_time=content_instance.completion_time,
        order=content_instance.order,
    )


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
    return ContentFetch(
        id=content_instance.id,
        title=content_instance.title,
        description=content_instance.description,
        content_type=content_instance.content_type,
        file_url=content_instance.file_url,
        completion_time=content_instance.completion_time,
        order=content_instance.order,
    )

def fetch_by_content_unit(content_unit_id: int, db: Session) -> list[ContentFetch]:
    content_unit = db.get(UnitContents, content_unit_id)
    if not content_unit:
        raise NoResultFound(f"No content unit with id {content_unit_id}")
    content_units = db.exec(
        select(Contents)
        .options(selectinload(Contents.unit_content))
        .where(Contents.content_unit_id == content_unit_id)
    )
    return [
        ContentFetch(
        id=content_unit.id,
        title=content_unit.title,
        description=content_unit.description,
        content_type=content_unit.content_type,
        file_url=content_unit.file_url,
        completion_time=content_unit.completion_time,
        order=content_unit.order,
    )for content_unit in content_units]
