import os

from app.constants import DetectionItemType
from app.schemas.detection import DetectionItemCreate
from app.services import FileStorageService


AVAILABLE_IMAGE_EXTENSIONS = set([
    ".jpg",
    ".jpeg",
])
AVAILABLE_VIDEO_EXTENSIONS = set([
    ".mp4",
    ".avi",
])


async def get_file_type(file_extension: str) -> bool:
    if file_extension in AVAILABLE_VIDEO_EXTENSIONS:
        return DetectionItemType.VIDEO

    if file_extension in AVAILABLE_IMAGE_EXTENSIONS:
        return DetectionItemType.IMAGE


async def check_files_extension(files: list) -> list[tuple[str, str]]:
    files_and_types = []
    uploaded_files = set()
    for file in files:
        if file in uploaded_files:
            continue
        file_type = ""
        _, file_extension = os.path.splitext(file.filename)
        
        if (
            file_extension not in AVAILABLE_IMAGE_EXTENSIONS and 
            file_extension not in AVAILABLE_VIDEO_EXTENSIONS
        ):
            continue

        file_type = await get_file_type(file_extension)
        uploaded_files.add(file)
        files_and_types.append((file, file_type))
    return files_and_types


async def create_items(
    file_service: FileStorageService,
    session,
    detection_item_repository,
    detection_task_uuid,
    upload_files,
) -> None:
    for file, type in upload_files:
        path = await file_service.save(detection_task_uuid, file)
        schema = DetectionItemCreate(
            origin_file=str(path),
            type=type,
            detection_id=detection_task_uuid,
        )
        await detection_item_repository.create(session, obj_in=schema)
