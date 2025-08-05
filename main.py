from fastapi import FastAPI

from app.db.session.initialize import init_db

from app.api.v1.routers.auth import auth_router
from app.api.v1.routers.users import user_router

app = FastAPI()
init_db()

app.include_router(auth_router)
app.include_router(user_router)