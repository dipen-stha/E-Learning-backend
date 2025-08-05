from sqlmodel import SQLModel

from app.db.session.session import engine


def init_db():
    SQLModel.metadata.create_all(engine)
