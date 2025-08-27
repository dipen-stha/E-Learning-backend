from uuid import uuid4

from fastapi import UploadFile

from config import CONTENT_DIR, COURSES_DIR, settings


async def image_save(file: UploadFile) -> str:
    file_path = None
    ext = file.filename.split(".")[-1]
    unique_name = f"{uuid4()}.{ext}"
    if file.content_type.startswith("video/"):
        file_path = f"{CONTENT_DIR}/{unique_name}"
    else:
        file_path = f"{COURSES_DIR}/{unique_name}"
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    return file_path


def format_file_path(image_url: str):
    if not image_url:
        return None
    return settings.API_DOMAIN + image_url
