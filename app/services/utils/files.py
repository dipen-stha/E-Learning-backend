from fastapi import HTTPException, UploadFile
from pydantic import ValidationError
from uuid import uuid4

from config import COURSES_DIR, settings


async def image_save(file: UploadFile) -> str:
    if not file.content_type.startswith("image/"):
        raise ValidationError("File must be an image")

    ext = file.filename.split(".")[-1]
    unique_name = f"{uuid4()}.{ext}"
    file_path = COURSES_DIR / unique_name

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    return file_path

def format_file_path(image_url: str):
    if not image_url:
        return None
    return settings.API_DOMAIN + image_url