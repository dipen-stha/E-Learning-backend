from typing import Annotated

import stripe

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from sqlalchemy.exc import NoResultFound
from sqlmodel import Session, select
from starlette.responses import JSONResponse

from app.api.v1.schemas.enrollment import (
    CourseEnrollmentCreate,
    CourseEnrollmentUpdate,
    PaymentIntentResponse,
)
from app.db.crud.enrollment import (
    course_enrollment_create,
    course_enrollment_payment_update,
    fetch_user_enrollments,
    fetch_user_enrollments_by_course,
)
from app.db.models.courses import Course
from app.db.models.enrollment import CourseEnrollment
from app.db.models.users import User
from app.db.session.session import get_db
from app.services.auth.core import get_current_user
from app.services.enum.courses import PaymentStatus
from config import settings


enrollment_router = APIRouter(prefix="/enrollment", tags=["Enrollment"])
stripe.api_key = settings.STRIPE_SECRET_KEY


@enrollment_router.post("/create-enrollment-session/")
def create_enrollment_session(
    data: CourseEnrollmentCreate, db: Annotated[Session, Depends(get_db)]
):
    try:
        course_id = data.course_id
        user_id = data.user_id
        existing_enrollment = db.exec(
            select(CourseEnrollment).where(
                CourseEnrollment.course_id == course_id,
                CourseEnrollment.user_id == user_id,
                CourseEnrollment.status != PaymentStatus.REJECTED,
            )
        ).first()
        if existing_enrollment and existing_enrollment.status == PaymentStatus.PAID:
            raise HTTPException(
                status_code=400, detail="Already enrolled to this course"
            )
        elif (
            existing_enrollment and existing_enrollment.status == PaymentStatus.PENDING
        ):
            raise HTTPException(
                status_code=400, detail="Your payment is being processed. Please wait!"
            )
        course_instance = db.get(Course, course_id)
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": data.currency,
                        "product_data": {"name": f"{course_instance.title}"},
                        "unit_amount": round(data.amount * 100),
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url="http://localhost:5173/sucess?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="http://localhost:5173/cancel",
            metadata={"course_id": course_id or ""},
        )
        payment = course_enrollment_create(
            enrollment_data=data,
            provider_payment_id=session.id,
            metadata=session.to_dict(),
            db=db,
        )
        return {"session_id": session.id, "url": session.url, "payment_id": payment.id}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_type": e.__class__.__name__, "error_message": str(e)},
        )


@enrollment_router.post("/create-payment-intent/")
def create_course_enrollment(
    enrollment_data: CourseEnrollmentCreate, db: Annotated[Session, Depends(get_db)]
):
    try:
        intent = stripe.PaymentIntent.create(
            amount=enrollment_data.amount,
            currency=enrollment_data.currency,
            metadata={"order_id": enrollment_data.course_id or ""},
        )
        payment = course_enrollment_create(
            enrollment_data=enrollment_data,
            provider_payment_id=intent.id,
            metadata=intent.to_dict(),
            db=db,
        )
        return PaymentIntentResponse(
            client_secret=intent.client_secret, enrollment_id=payment.id
        )
    except ValidationError as ve:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({"errors": ve.errors()}),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "detail_type": e.__class__.__name__,
                "message": str(e),
            },
        )


@enrollment_router.post("/webhook/")
async def stripe_payment_webhook(
    request: Request, db: Annotated[Session, Depends(get_db)]
):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        payment_done = False
        if event["type"] == "checkout.session.completed":
            intent = event["data"]["object"]
            enrollment_update_data = CourseEnrollmentUpdate(status=PaymentStatus.PAID)
            course_enrollment_payment_update(
                intent.get("id"), enrollment_update_data, db
            )
            payment_done = True

        elif event["type"] == "checkout.session.expired":
            intent = event["data"]["object"]
            enrollment_update_data = CourseEnrollmentUpdate(
                status=PaymentStatus.REJECTED,
                failure_code=event["data"]["failure_code"],
                failure_message=event["data"]["failure_message"],
            )
            course_enrollment_payment_update(
                intent.get("id"), enrollment_update_data, db
            )
            payment_done = False

        return {"status": payment_done}
    except stripe.error.SignatureVerificationError:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content="Invalid Signature",
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail_type": e.__class__.__name__,
                "message": str(e),
            },
        )


@enrollment_router.get("/user-fetch-by-course/{course_id}/")
def user_enrollment_by_course_id(
    course_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        return fetch_user_enrollments_by_course(user.id, course_id, db)
    except ValidationError as ve:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({"errors": ve.errors()}),
        )
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such course"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "detail_type": e.__class__.__name__,
                "message": str(e),
            },
        )


@enrollment_router.get("/user-enrolled-courses/")
def fetch_enrolled_courses(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return fetch_user_enrollments(user.id, db)
    except ValidationError as ve:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({"errors": ve.errors()}),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "detail_type": e.__class__.__name__,
                "message": str(e),
            },
        )
