from pydantic import BaseModel, Field

class FilterParams(BaseModel):
    limit: int | None = Field(ge=0, le=100, default=None)
    offset: int | None = Field(default=None, ge=0)
    page: int | None = Field(default=None, ge=0)