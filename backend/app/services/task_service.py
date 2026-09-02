from fastapi import APIRouter
from app.db.database import get_connection
from app.schemas.tasks import TaskCreate, TaskUpdate
from app.api.auth import get_current_user
from fastapi import Depends
from app.db.redis import redis_client
import json
from app.core.logger import logger


router = APIRouter(prefix="/api/tasks", tags=["tasks"])



def create_task_service(task: TaskCreate, user_id: int):
    conn = get_connection()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO tasks (title, description, user_id)
                VALUES (%s, %s, %s)
                RETURNING id, title, description, status, user_id
                """,
                (task.title, task.description, user_id),
            )
            result = cursor.fetchone()
    conn.close()
    redis_client.delete(f"tasks:user:{user_id}")
    return {
        "id": result[0],
        "title": result[1],
        "description": result[2],
        "status": result[3],
        "user_id": result[4],
    }

def update_task_service(task_id: int, task: TaskUpdate, user_id: int):
    conn = get_connection()

    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE tasks
                SET
                    title = COALESCE(%s, title),
                    description = COALESCE(%s, description),
                    status = COALESCE(%s, status),
                    updated_at = CURRENT_TIMESTAMP
                where id = %s AND user_id = %s
                RETURNING id, title, description, status
                """,
                (
                    task.title,
                    task.description,
                    task.status,
                    task_id,
                    user_id
                ),
            )
            result = cursor.fetchone()

    conn.close()
    redis_client.delete(f"tasks:user:{user_id}")
    if result is None:
        return {"message": "任务不存在"}
    return {
        "id": result[0],
        "title": result[1],
        "description": result[2],
        "status": result[3],
    }


def delete_task_service(task_id: int, user_id: int):
    conn = get_connection()

    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM tasks
                WHERE id = %s AND user_id = %s
                RETURNING id
                """,
                (task_id, user_id),
            )

            result = cursor.fetchone()

    conn.close()
    redis_client.delete(f"tasks:user:{user_id}")
    if result is None:
        return {"message": "任务不存在"}

    return {
        "message": "删除成功",
        "id": result[0],
    }

# 查询
def get_tasks_service(user_id: int):
# 先在redis查询
    cache_key = f"tasks:user:{user_id}"
    cached_tasks = redis_client.get(cache_key)
    if cached_tasks:
        logger.info(
            "cache hit: %s",
            cache_key,
        )
        return json.loads(cached_tasks)  # 将字符串转换回列表
    
    conn = get_connection()

    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    id,
                    title,
                    description,
                    status,
                    created_at,
                    updated_at,
                    user_id
                FROM tasks
                WHERE user_id = %s
                ORDER BY id DESC
                """,
                (user_id,),
            )

            rows = cursor.fetchall()
    conn.close()

    tasks = []

    for row in rows:
        tasks.append(
            {
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "status": row[3],
                "created_at": row[4].isoformat() if row[4] else None,
                "updated_at": row[5].isoformat() if row[5] else None,
                "user_id": row[6],
            }
        )
    redis_client.set(cache_key, json.dumps(tasks), ex=60)  # 设置过期时间为60秒
    return tasks