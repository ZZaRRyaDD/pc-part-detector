import uuid
import urllib

from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Path,
    Request,
    responses,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.constants import DetectionTaskStatus
from app.db.connection import get_session
from app.db.repository import DetectionItemRepository, DetectionTaskRepository
from app.schemas.detection import DetectionTaskBase, DetectionTaskCompleted
from app.tasks import run_detection
from app.utils.detection import (
    archive_detection_task,
    check_files_extension,
    create_items,
)


api_router = APIRouter(
    prefix="/detection",
    tags=["Detection"],
)


@api_router.post(
    "",
    response_model=DetectionTaskBase,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Files extensions is'not valid",
        },
    },
)
async def create_detection_task(
    request: Request,
    files: list[UploadFile] = Form(...),
    session: AsyncSession = Depends(get_session),
):
    upload_files = await check_files_extension(files)
    if not upload_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Files extensions is'not valid",
        )
    
    detection_task_repository = DetectionTaskRepository()
    detection_item_repository = DetectionItemRepository()

    detection_task = await detection_task_repository.create(session, obj_in={})
    await create_items(
        request.app.state.file_service,
        session,
        detection_item_repository,
        str(detection_task.id),
        upload_files,
    )
    run_detection.delay(str(detection_task.id))
    return detection_task


@api_router.get(
    "/{detection_id}",
    response_model=DetectionTaskCompleted,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "Задача детекции не найдена",
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Детекция не завершена",
        },
    },
)
async def get_detection_task(
    _: Request,
    detection_id: str = Path(...),
    session: AsyncSession = Depends(get_session),
):
    task_repository = DetectionTaskRepository()
    task = await task_repository.get(session, detection_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача детекции не найдена",
        )
    if task.status == DetectionTaskStatus.CREATED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Детекция не завершена",
        )
    settings = get_settings()
    base_url = f"http://localhost:{settings.APP_PORT}{settings.PATH_PREFIX}/"
    for item in task.detection_items:
        item.origin_file = urllib.parse.urljoin(base_url, item.origin_file)
        item.predict_file = urllib.parse.urljoin(base_url, item.predict_file)
    return task


@api_router.get(
    "/{uuid}/download",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "Detection not found",
        },
    },
)
async def download_detection_task(
    _: Request,
    uuid: uuid.UUID = Path(...),
    session: AsyncSession = Depends(get_session),
):
    task_repository = DetectionTaskRepository()
    task = await task_repository.get(session, uuid)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detection not found",
        )

    zip_bytes_io = await archive_detection_task(task)
    filename = f"{uuid}.zip"

    response = responses.StreamingResponse(
        iter([zip_bytes_io.getvalue()]),
        media_type="application/x-zip-compressed",
        headers={
            "Content-Disposition": f"attachment;filename={filename}",
            "Content-Length": str(zip_bytes_io.getbuffer().nbytes),
        }
    )
    zip_bytes_io.close()
    return response
