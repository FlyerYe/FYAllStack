from fastapi import APIRouter
from app.schemas.tasks import TaskCreate, TaskUpdate
from app.core.security import CurrentUser, get_current_user
from fastapi import Depends
from app.services.task_service import create_task_service, update_task_service, delete_task_service, get_tasks_service

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("")
def create_task(
    task: TaskCreate,
    current_user: CurrentUser = Depends(get_current_user),
):
    return create_task_service(task, current_user["user_id"])

@router.put("/{task_id}")
def update_task(
    task_id: int,
    task: TaskUpdate,
    current_user: CurrentUser = Depends(get_current_user),
):
    return update_task_service(task_id, task, current_user["user_id"])

@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    current_user: CurrentUser = Depends(get_current_user),
):
    return delete_task_service(task_id, current_user["user_id"])

# 查询
@router.get("")
def get_tasks(current_user: CurrentUser = Depends(get_current_user)):
    return get_tasks_service(current_user["user_id"])
