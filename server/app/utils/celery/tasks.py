import shutil
from pathlib import Path

from app.config import get_settings
from app.constants import DetectionTaskStatus
from app.db.connection import SessionManager
from app.db.repository import DetectionItemRepository, DetectionTaskRepository
from app.services import YOLOWrapper


async def remove_old_detections():
    session_maker = SessionManager().get_session_maker()
    async with session_maker() as session:

        detection_task_repository = DetectionTaskRepository()
        detection_item_repository = DetectionItemRepository()

        old_detection_tasks = await detection_task_repository.get_old_tasks(session)

        settings = get_settings()
        for task in old_detection_tasks:
            for item in task.detection_items:
                await detection_item_repository.remove(
                    session,
                    obj_id=item.id
                )
            path = Path(settings.MEDIA_PATH) / str(task.id)
            shutil.rmtree(path.absolute())
            await detection_task_repository.remove(session, obj_id=task.id)


async def run_detection(uuid: str, model: YOLOWrapper):
    session_maker = SessionManager().get_session_maker()
    async with session_maker() as session:

        detection_task_repository = DetectionTaskRepository()
        detection_item_repository = DetectionItemRepository()

        detection_task = await detection_task_repository.get(session, obj_id=uuid)
        for item in detection_task.detection_items:
            result = model.functions[item.type](item.origin_file, uuid)
            obj = {
                "predict_file": result['result_path'],
                "classes": ",".join(set(result['classes'])),
            }
            await detection_item_repository.update(
                session,
                db_obj=item,
                obj_in=obj,
            )
        updated_detection = {
            "status": DetectionTaskStatus.FINISHED,
        }
        await detection_task_repository.update(
            session,
            db_obj=detection_task,
            obj_in=updated_detection,
        )
