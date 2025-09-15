from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.staticfiles import StaticFiles

from app.api.v1.routers.auth import auth_router
from app.api.v1.routers.common import common_router
from app.api.v1.routers.courses import course_router
from app.api.v1.routers.enrollment import enrollment_router
from app.api.v1.routers.users import user_router
from app.api.v1.routers.assessments import assessments_router
from app.db.session.initialize import init_db
from config import settings


app = FastAPI()
init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)
app.add_middleware(GZipMiddleware, compresslevel=5)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(course_router)
app.include_router(common_router)
app.include_router(enrollment_router)
app.include_router(assessments_router)

app.mount("/media", StaticFiles(directory="media"), name="media")
