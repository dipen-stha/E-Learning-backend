from app.api.v1.routers.auth import auth_router
from app.api.v1.routers.courses import course_router
from app.api.v1.routers.users import user_router
from app.db.session.initialize import init_db

from fastapi import FastAPI


app = FastAPI()
init_db()

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(course_router)
