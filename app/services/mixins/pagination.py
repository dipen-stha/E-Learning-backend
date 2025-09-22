from math import ceil

from sqlalchemy.exc import InvalidRequestError
from sqlmodel import Session, select, func

from app.api.v1.schemas.extras import FilterParams


class PaginationMixin:
    def __init__(self):
        self.total_pages = 0
        self.current_page = 0

    def paginate_query(self, statement, params: FilterParams, db: Session):
        if params.offset is None or params.limit is None:
            raise InvalidRequestError("offset and limit are required")
        total_items = db.exec(select(func.count()).select_from(statement.subquery())).one()
        data = db.exec(statement.offset(params.offset).limit(params.limit)).all()
        self.total_pages = ceil(total_items / params.page) if total_items else 0
        self.current_page = (params.offset // params.limit) + 1
        return data

    def paginate_response(self, response):
        return {
            "data": response,
            "total_pages": self.total_pages,
            "current_page": self.current_page,
        }