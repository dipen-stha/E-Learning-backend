from fastapi import UploadFile
from sqlalchemy import exists
from sqlalchemy.exc import InvalidRequestError, NoResultFound
from sqlalchemy.orm import joinedload, selectinload
from sqlmodel import Session, case, delete, desc, distinct, func, select

from app.api.v1.schemas.courses import (
    BaseCourse,
    BaseSubjectFetch,
    BaseUnit,
    CategoryFetch,
    ContentCreate,
    ContentFetch,
    ContentUpdate,
    CourseCreate,
    CourseDetailFetch,
    CourseFetch,
    CourseUpdate,
    LatestCourseFetch,
    SubjectCreate,
    SubjectDetailedFetch,
    SubjectFetch,
    SubjectUpdate,
    UnitCreate,
    UnitFetch,
    UnitUpdate,
    UnitWithContents,
    VideoTimeStamps,
)
from app.api.v1.schemas.users import ProfileSchema
from app.db.models.common import UserSubject
from app.db.models.courses import (
    Category,
    CategoryCourseLink,
    Contents,
    ContentVideoTimeStamp,
    Course,
    CourseRating,
    Subject,
    Unit,
)
from app.db.models.enrollment import CourseEnrollment
from app.db.models.users import Profile, User
from app.services.enum.courses import PaymentStatus, StatusEnum
from app.services.utils.crud_utils import update_model_instance
from app.services.utils.date_utils import format_to_mm_ss, format_to_seconds
from app.services.utils.files import format_file_path, image_save


def course_category_create(title: str, db: Session) -> CategoryFetch:
    category_instance = Category(title=title)
    db.add(category_instance)
    db.commit()
    db.refresh(category_instance)
    return CategoryFetch.model_validate(category_instance)


def get_all_categories(db: Session) -> list[CategoryFetch]:
    categories = db.exec(select(Category)).all()
    return [CategoryFetch.model_validate(category) for category in categories]


def list_minimal_courses(db: Session) -> list[BaseCourse]:
    courses = db.exec(
        select(Course.id, Course.title).where(Course.status == StatusEnum.PUBLISHED)
    ).all()
    return [
        BaseCourse(
            id=course.id,
            title=course.title,
        )
        for course in courses
    ]


def fetch_latest_courses(
    db: Session, user_id: int | None = None
) -> list[LatestCourseFetch]:
    student_count_expr = func.count(CourseEnrollment.user_id).label("student_count")
    rating_calculate_expr = func.avg(CourseRating.rating)
    statement = (
        select(Course, student_count_expr, rating_calculate_expr)
        .select_from(Course)
        .join(CourseEnrollment, CourseEnrollment.course_id == Course.id, isouter=True)
        .join(CourseRating, CourseRating.course_id == Course.id, isouter=True)
        .join(User, Course.instructor_id == User.id)
        .join(Profile, User.id == Profile.id)
        .options(selectinload(Course.instructor).selectinload(User.profile))
        .order_by(desc(Course.created_at))
        .group_by(Course.id)
    )
    if user_id:
        statement = statement.where(
            ~exists()
            .where(
                (CourseEnrollment.course_id == Course.id)
                & (CourseEnrollment.user_id == user_id)
            )
            .correlate(Course)
        )
    latest_courses = db.exec(statement).all()
    return [
        LatestCourseFetch(
            id=course.id,
            title=course.title,
            price=course.price,
            completion_time=course.completion_time,
            student_count=student_count,
            course_rating=course_rating,
            image_url=format_file_path(course.image_url),
            instructor_name=course.instructor.profile.name,
        )
        for course, student_count, course_rating in latest_courses[:5]
    ]


def list_all_courses(db: Session) -> list[CourseDetailFetch]:
    student_count_expr = func.count(distinct(User.id)).label("student_count")
    rating_calculate_expr = func.avg(CourseRating.rating)
    total_revenue = (
        Course.price
        * func.count(
            distinct(
                case(
                    (
                        CourseEnrollment.status == PaymentStatus.PAID,
                        CourseEnrollment.user_id,
                    )
                )
            )
        )
    ).label("total_revenue")
    courses = db.exec(
        select(Course, student_count_expr, rating_calculate_expr, total_revenue)
        .select_from(Course)
        .join(CourseEnrollment, CourseEnrollment.course_id == Course.id, isouter=True)
        .join(User, User.id == CourseEnrollment.user_id, isouter=True)
        .join(CourseRating, CourseRating.course_id == Course.id, isouter=True)
        .join(Subject, Subject.course_id == Course.id, isouter=True)
        .options(
            selectinload(Course.categories),
            selectinload(Course.instructor).selectinload(User.profile),
            selectinload(Course.subjects),
        )
        .group_by(Course.id, Course.price)
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
            total_revenue=total_revenue,
            instructor=(
                ProfileSchema(
                    name=course.instructor.profile.name,
                    dob=course.instructor.profile.dob,
                    gender=course.instructor.profile.gender,
                    avatar=format_file_path(course.instructor.profile.avatar),
                )
            ),
            categories=[
                CategoryFetch(id=category.id, title=category.title)
                for category in course.categories
            ],
            image_url=format_file_path(course.image_url),
            subjects=[subject.title for subject in course.subjects],
            status=course.status,
        )
        for course, student_count, course_rating, total_revenue in courses
    ]
    return courses_data


async def course_create(
    course: CourseCreate, db: Session, file: UploadFile
) -> CourseFetch:
    data = course.model_dump()
    if file:
        image_path = await image_save(file)
        data["image_url"] = str(image_path)
    categories_id = data.pop("categories_id")
    statement = select(Category.id).where(Category.id.in_(categories_id))
    categories = db.exec(statement).all()
    course_instance = Course(**data)
    db.add(course_instance)
    db.flush()
    if categories:
        course_categories_link = [
            CategoryCourseLink(course_id=course_instance.id, category_id=category)
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


async def course_update(
    course_id: int,
    course_data: CourseUpdate,
    db: Session,
    file: UploadFile | None = None,
) -> BaseCourse:
    try:
        course_instance = db.get(Course, course_id)
        if not course_instance:
            raise NoResultFound("Course not found")
        payload_data = course_data.model_dump(exclude_none=True)
        categories_id = payload_data.pop("categories_id")
        if file:
            image_path = await image_save(file)
            payload_data["image_url"] = str(image_path)
        updated_course_instance = update_model_instance(course_instance, payload_data)
        db.add(updated_course_instance)

        if categories_id:
            db.exec(
                delete(CategoryCourseLink).where(
                    CategoryCourseLink.course_id == course_id
                )
            )
            new_categories_links = [
                CategoryCourseLink(category_id=cat_id, course_id=course_id)
                for cat_id in categories_id
            ]
            db.add_all(new_categories_links)

        db.commit()
        db.refresh(updated_course_instance)
        return BaseCourse(
            id=updated_course_instance.id,
            title=updated_course_instance.title,
        )
    except Exception as e:
        db.rollback()
        raise e


def course_fetch_by_id(course_id: int, db: Session):
    course = db.get(Course, course_id)
    if not course:
        raise NoResultFound(f"Course with pk {course_id} not found")
    statement = (
        select(
            Course,
            func.count(CourseEnrollment.user_id)
            .filter(CourseEnrollment.status == PaymentStatus.PAID)
            .label("student_count"),
            func.avg(CourseRating.rating).label("course_rating"),
        )
        .join(CourseEnrollment, CourseEnrollment.course_id == Course.id, isouter=True)
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
                id=course.instructor.id,
                name=course.instructor.profile.name,
                dob=course.instructor.profile.dob,
                gender=course.instructor.profile.gender,
                avatar=format_file_path(course.instructor.profile.avatar),
            )
        ),
        course_rating=course_rating,
        student_count=student_count,
        categories=[
            CategoryFetch(id=category.id, title=category.title)
            for category in course.categories
        ],
        image_url=format_file_path(course.image_url),
        status=course.status,
        subjects=[
            SubjectFetch(
                id=subject.id,
                title=subject.title,
                completion_time=subject.completion_time,
                order=subject.order,
                units=[unit.title for unit in subject.units],
                status=subject.status,
            )
            for subject in course.subjects
        ],
    )


def subject_create(subject: SubjectCreate, db: Session) -> SubjectFetch:
    data = subject.model_dump()
    course_id = data.get("course_id")
    course = db.exec(select(Course).where(Course.id == course_id)).first()
    order = data.get("order")
    db.exec(
        select(Subject.id).where(Subject.course_id == course.id, Subject.order == order)
    ).first()
    if order:
        raise InvalidRequestError(
            "Another subject is already assigned to this order number."
        )
    if not course:
        raise NoResultFound(f"No course with id {course_id}")
    subject_instance = Subject(**data)
    db.add(subject_instance)
    db.commit()
    db.refresh(subject_instance)
    return SubjectFetch.model_validate(subject_instance)


def subject_update(subject_id: int, subject: SubjectUpdate, db: Session):
    data = subject.model_dump(exclude_none=True)
    course_id = data.get("course_id")
    subject = db.get(Subject, subject_id)
    if not subject:
        raise NoResultFound(f"No subject with id {subject_id}")
    course = db.get(Course, course_id)
    if not course:
        raise NoResultFound(f"No course with id {course_id}")
    order = data.get("order")
    existing_instance = db.exec(
        select(Subject).where(
            Subject.course_id == course.id,
            Subject.order == order,
            Subject.id != subject_id,
        )
    ).first()
    if existing_instance:
        raise InvalidRequestError(
            f"{existing_instance.title} was assigned the order number {order}"
        )
    updated_subject_instance = update_model_instance(subject, data)
    db.add(updated_subject_instance)
    db.commit()
    db.refresh(updated_subject_instance)
    return updated_subject_instance


def fetch_subjects_by_courses(
    db: Session, course_id: int | None = None
) -> list[SubjectFetch]:

    statement = (
        select(Subject)
        .join(UserSubject, isouter=True)
        .options(
            joinedload(Subject.course)
            .joinedload(Course.instructor)
            .joinedload(User.profile)
        )
        .order_by(Subject.course_id, Subject.order)
    )
    if course_id:
        statement = statement.where(Subject.course_id == course_id)
    subjects = db.exec(statement).all()
    subjects_data = [
        SubjectFetch(
            id=subject.id,
            title=subject.title,
            description=subject.description,
            course=subject.course,
            instructor=subject.course.instructor.profile,
            status=subject.status,
            order=subject.order,
        )
        for subject in subjects
    ]
    return subjects_data


def fetch_subjects_minimal(
    db: Session, course_id: int | None = None
) -> list[BaseSubjectFetch]:
    statement = select(Subject.id, Subject.title).where(
        Subject.status == StatusEnum.PUBLISHED
    )
    if course_id:
        statement = statement.where(Subject.course_id == course_id)
    subjects = db.exec(statement).all()
    subjects_data = [
        BaseSubjectFetch(id=subject.id, title=subject.title) for subject in subjects
    ]
    return subjects_data


def subject_fetch_by_id(subject_id: int, db: Session):
    subject = db.get(Subject, subject_id)
    if not subject:
        raise NoResultFound(f"Subject with pk {subject_id} not found")

    statement = (
        select(Subject)
        .options(
            selectinload(Subject.course),
            selectinload(Subject.units)
            .selectinload(Unit.contents)
            .selectinload(Contents.video_time_stamps),
        )
        .where(Subject.id == subject.id)
    )
    subject_instance = db.exec(statement).first()
    return SubjectDetailedFetch(
        id=subject_instance.id,
        title=subject_instance.title,
        course=BaseCourse(
            id=subject_instance.course.id, title=subject_instance.course.title
        ),
        order=subject_instance.order,
        description=subject_instance.description,
        status=subject_instance.status,
        objectives=subject_instance.objectives,
        units=[
            UnitWithContents(
                id=unit.id,
                title=unit.title,
                completion_time=unit.completion_time,
                contents=[
                    ContentFetch(
                        id=content.id,
                        title=content.title,
                        completion_time=content.completion_time,
                        order=content.order,
                        content_type=content.content_type,
                        status=content.status,
                        file_url=format_file_path(content.file_url),
                        video_time_stamps=[
                            VideoTimeStamps(
                                id=stamp.id,
                                title=stamp.title,
                                time_stamp=stamp.time_stamp,
                            )
                            for stamp in content.video_time_stamps
                        ],
                    )
                    for content in unit.contents
                ],
            )
            for unit in subject_instance.units
        ],
        completion_time=subject_instance.completion_time,
    )


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
    return UnitFetch(
        id=unit_instance.id,
        title=unit_instance.title,
        description=unit_instance.description,
        objectives=unit_instance.objectives,
        status=unit_instance.status,
        completion_time=unit_instance.completion_time,
        order=unit_instance.order,
    )


def unit_update(unit_id: int, unit: UnitUpdate, db: Session) -> UnitFetch:
    data = unit.model_dump()
    unit_instance = db.exec(select(Unit).where(Unit.id == unit_id)).first()
    order = data.get("order")
    subject_id = data.get("subject_id")
    if not unit_instance:
        raise NoResultFound(f"No unit with id {unit_id}")
    if subject_id:
        subject = db.get(Subject, subject_id)
        if not subject:
            raise NoResultFound(f"No subject with id {unit_id}")
    if order:
        existing_unit_with_given_order = db.exec(
            select(Unit).where(
                Unit.order == order, Unit.subject_id == subject_id, Unit.id != unit_id
            )
        ).first()
        if existing_unit_with_given_order:
            raise InvalidRequestError(
                f"Unit with order {order} already assigned to unit: {existing_unit_with_given_order.id}"
            )
    updated_unit_instance = update_model_instance(unit_instance, data)
    db.add(updated_unit_instance)
    db.commit()
    db.refresh(updated_unit_instance)
    return updated_unit_instance


def fetch_all_units(db: Session) -> list[UnitFetch]:
    statement = (
        select(Unit, Subject, Course)
        .join(Subject, Subject.id == Unit.subject_id)
        .join(Course, Subject.course_id == Course.id)
        .order_by(Course.id, Subject.id, Unit.order)
    )
    units = db.exec(statement).all()
    return [
        UnitFetch(
            id=unit.id,
            title=unit.title,
            subject=subject,
            order=unit.order,
            description=unit.description,
            objectives=unit.objectives,
            course=course,
            completion_time=unit.completion_time,
            status=unit.status,
        )
        for unit, subject, course in units
    ]


def fetch_unit_by_id(unit_id: int, db: Session):
    statement = (
        select(Unit)
        .options(joinedload(Unit.subject).joinedload(Subject.course))
        .where(Unit.id == unit_id)
    )
    unit_instance = db.exec(statement).first()
    if not unit_instance:
        raise NoResultFound(f"No unit with id {unit_id}")
    return UnitFetch(
        id=unit_instance.id,
        title=unit_instance.title,
        description=unit_instance.description,
        order=unit_instance.order,
        completion_time=unit_instance.completion_time,
        subject=BaseSubjectFetch(
            id=unit_instance.subject.id, title=unit_instance.subject.title
        ),
        course=BaseCourse(
            id=unit_instance.subject.course.id, title=unit_instance.subject.course.title
        ),
        status=unit_instance.status,
        objectives=unit_instance.objectives,
    )


def fetch_units_by_subject(subject_id: int, db: Session) -> list[UnitFetch]:
    units = db.exec(select(Unit).options(selectinload(Unit.subject)))
    return [UnitFetch.from_orm(unit) for unit in units]


def fetch_minimal_units(db: Session, subject_id: int | None = None) -> list[BaseUnit]:
    statement = select(Unit.id, Unit.title)
    if subject_id:
        statement = statement.where(Unit.subject_id == subject_id)
    units = db.exec(statement).all()
    return [BaseUnit(id=unit.id, title=unit.title) for unit in units]


async def content_create(
    content: ContentCreate, db: Session, file: UploadFile
) -> ContentFetch:
    data = content.model_dump()
    file_path = await image_save(file)
    data["file_url"] = file_path
    video_time_stamps = data.pop("video_time_stamps")
    unit_id = data.get("unit_id")
    unit_instance = db.get(Unit, unit_id)
    if not unit_instance:
        raise NoResultFound(f"No unit with id {unit_id}")
    content_instance = Contents(**data)
    db.add(content_instance)
    db.flush()
    time_stamp_instances = [
        ContentVideoTimeStamp(
            content_id=content_instance.id,
            title=item.get("title"),
            time_stamp=format_to_seconds(item.get("time_stamp")),
        )
        for item in video_time_stamps
    ]
    db.add_all(time_stamp_instances)
    db.commit()
    return ContentFetch(
        id=content_instance.id,
        title=content_instance.title,
        description=content_instance.description,
        content_type=content_instance.content_type,
        file_url=content_instance.file_url,
        completion_time=content_instance.completion_time,
        order=content_instance.order,
        status=content_instance.status,
    )


async def content_update(
    content_id: int, content: ContentUpdate, db: Session, file: UploadFile | None = None
) -> ContentFetch:
    try:
        data = content.model_dump(exclude_none=True)
        unit_id = data.get("unit_id")
        order = data.get("order")
        content_instance = db.get(Contents, content_id)
        video_time_stamps = (
            data.pop("video_time_stamps") if "video_time_stamps" in data else None
        )
        if unit_id:
            unit_instance = db.get(Unit, unit_id)
            if not unit_instance:
                raise NoResultFound(f"No unit with id {unit_id}")
        if order:
            existing_content_by_order = db.exec(
                select(Contents).where(
                    Contents.id != content_id,
                    Contents.unit_id == unit_id,
                    Contents.order == order,
                )
            ).all()
            if existing_content_by_order:
                raise InvalidRequestError(
                    f"Content in unit {unit_id} already has a content in order {order}"
                )
        if file:
            image_path = await image_save(file)
            data["file_url"] = str(image_path)

        updated_instance = update_model_instance(content_instance, data)
        db.add(updated_instance)
        if video_time_stamps:
            db.exec(
                delete(ContentVideoTimeStamp).where(
                    ContentVideoTimeStamp.content_id == content_id
                )
            )
            new_video_time_stamps = [
                ContentVideoTimeStamp(
                    content_id=content_instance.id,
                    title=item.get("title"),
                    time_stamp=format_to_seconds(item.get("time_stamp")),
                )
                for item in video_time_stamps
            ]
            db.add_all(new_video_time_stamps)

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
            status=content_instance.status,
        )
    except Exception as ex:
        db.rollback()
        raise ex


def fetch_contents(
    db: Session,
    unit_id: int | None = None,
    course_id: int | None = None,
    subject_id: int | None = None,
) -> list[ContentFetch]:
    statement = (
        select(Contents, User)
        .join(Unit, Unit.id == Contents.unit_id)
        .join(Subject, Subject.id == Unit.subject_id)
        .join(Course, Course.id == Subject.course_id)
        .join(User, Course.instructor_id == User.id)
        .options(
            selectinload(Contents.unit)
            .selectinload(Unit.subject)
            .selectinload(Subject.course)
            .selectinload(Course.instructor)
            .selectinload(User.profile)
        )
        .order_by(Course.id, Unit.id, Contents.order)
    )
    if unit_id:
        statement = statement.where(Contents.unit_id == unit_id)

    if course_id:
        statement = statement

    if subject_id:
        statement = statement

    contents = db.exec(statement).all()
    return [
        ContentFetch(
            id=content.id,
            title=content.title,
            completion_time=content.completion_time,
            order=content.order,
            course=content.unit.subject.course,
            subject=content.unit.subject,
            unit=content.unit,
            instructor=ProfileSchema(
                id=instructor.id,
                name=instructor.profile.name,
                avatar=format_file_path(instructor.profile.avatar),
            ),
            file_url=content.file_url,
            content_type=content.content_type,
            status=content.status,
        )
        for content, instructor in contents
    ]


def fetch_content_by_id(content_id: int, db: Session) -> ContentFetch:
    statement = (
        select(Contents)
        .options(
            joinedload(Contents.unit)
            .joinedload(Unit.subject)
            .joinedload(Subject.course),
            selectinload(Contents.video_time_stamps),
        )
        .where(Contents.id == content_id)
    )
    content_instance = db.exec(statement).first()
    return ContentFetch(
        id=content_instance.id,
        title=content_instance.title,
        description=content_instance.description,
        content_type=content_instance.content_type,
        course=BaseCourse(
            id=content_instance.unit.subject.course.id,
            title=content_instance.unit.subject.course.title,
        ),
        subject=BaseSubjectFetch(
            id=content_instance.unit.subject.id,
            title=content_instance.unit.subject.title,
        ),
        unit=BaseUnit(id=content_instance.unit.id, title=content_instance.unit.title),
        status=content_instance.status,
        completion_time=content_instance.completion_time,
        order=content_instance.order,
        file_url=format_file_path(content_instance.file_url),
        video_time_stamps=[
            VideoTimeStamps(
                id=time_stamp.id,
                title=time_stamp.title,
                time_stamp=format_to_mm_ss(time_stamp.time_stamp),
            )
            for time_stamp in content_instance.video_time_stamps
        ],
    )
