from __future__ import annotations

from decimal import Decimal

import psycopg
from fastapi import HTTPException

from app.core.security import CurrentUser
from app.db.database import get_connection
from app.schemas.orders import AdminOrderStatusUpdate, OrderCreate, OrderStatus


def _serialize_order(order_row: tuple, item_rows: list[tuple]) -> dict:
    items = []
    total_amount = Decimal("0")
    for row in item_rows:
        price = row[4]
        subtotal = price * row[3]
        total_amount += subtotal
        items.append(
            {
                "id": row[0],
                "recipe_id": row[1],
                "recipe_name": row[2],
                "image_url": row[5],
                "quantity": row[3],
                "price": price,
                "subtotal": subtotal,
            }
        )

    return {
        "id": order_row[0],
        "user_id": order_row[1],
        "status": order_row[2],
        "total_amount": total_amount,
        "created_at": order_row[3].isoformat() if order_row[3] else None,
        "updated_at": order_row[4].isoformat() if order_row[4] else None,
        "items": items,
    }


def get_order_service(order_id: int, user_id: int) -> dict:
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, user_id, status, created_at, updated_at
                    FROM orders
                    WHERE id = %s AND user_id = %s
                    """,
                    (order_id, user_id),
                )
                order_row = cursor.fetchone()
                if order_row is None:
                    raise HTTPException(status_code=404, detail="订单不存在")

                cursor.execute(
                    """
                    SELECT oi.id, oi.recipe_id, r.name, oi.quantity, oi.price, r.image_url
                    FROM order_items oi
                    JOIN recipes r ON r.id = oi.recipe_id
                    WHERE oi.order_id = %s
                    ORDER BY oi.id ASC
                    """,
                    (order_id,),
                )
                item_rows = cursor.fetchall()
        return _serialize_order(order_row, item_rows)
    finally:
        conn.close()


def create_order_service(order: OrderCreate, current_user: CurrentUser) -> dict:
    recipe_ids = [item.recipe_id for item in order.items]
    if len(recipe_ids) != len(set(recipe_ids)):
        raise HTTPException(status_code=400, detail="同一订单不能重复添加相同菜谱")

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM users WHERE id = %s",
                    (current_user["user_id"],),
                )
                if cursor.fetchone() is None:
                    raise HTTPException(status_code=401, detail="用户不存在")

                cursor.execute(
                    """
                    SELECT id, name, price, status
                    FROM recipes
                    WHERE id = ANY(%s)
                    FOR UPDATE
                    """,
                    (recipe_ids,),
                )
                recipe_rows = {row[0]: row for row in cursor.fetchall()}
                if any(
                    recipe_id not in recipe_rows
                    or recipe_rows[recipe_id][3] != "active"
                    for recipe_id in recipe_ids
                ):
                    raise HTTPException(status_code=400, detail="存在不存在或已下架的菜谱")

                cursor.execute(
                    """
                    INSERT INTO orders (user_id, status)
                    VALUES (%s, 'pending')
                    RETURNING id
                    """,
                    (current_user["user_id"],),
                )
                order_id = cursor.fetchone()[0]

                for item in order.items:
                    cursor.execute(
                        """
                        INSERT INTO order_items (order_id, recipe_id, quantity, price)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            order_id,
                            item.recipe_id,
                            item.quantity,
                            recipe_rows[item.recipe_id][2],
                        ),
                    )
        return get_order_service(order_id, current_user["user_id"])
    except psycopg.errors.ForeignKeyViolation as exc:
        raise HTTPException(status_code=401, detail="用户不存在") from exc
    finally:
        conn.close()


def get_orders_service(current_user: CurrentUser) -> list[dict]:
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, user_id, status, created_at, updated_at
                    FROM orders
                    WHERE user_id = %s
                    ORDER BY id DESC
                    """,
                    (current_user["user_id"],),
                )
                order_rows = cursor.fetchall()
                if not order_rows:
                    return []

                order_ids = [row[0] for row in order_rows]
                cursor.execute(
                    """
                    SELECT oi.id, oi.order_id, oi.recipe_id, r.name,
                           oi.quantity, oi.price, r.image_url
                    FROM order_items oi
                    JOIN recipes r ON r.id = oi.recipe_id
                    WHERE oi.order_id = ANY(%s)
                    ORDER BY oi.order_id, oi.id
                    """,
                    (order_ids,),
                )
                item_rows_by_order: dict[int, list[tuple]] = {}
                for row in cursor.fetchall():
                    item_rows_by_order.setdefault(row[1], []).append(
                        (row[0], row[2], row[3], row[4], row[5], row[6])
                    )
        return [
            _serialize_order(order_row, item_rows_by_order.get(order_row[0], []))
            for order_row in order_rows
        ]
    finally:
        conn.close()


def cancel_order_service(order_id: int, current_user: CurrentUser) -> dict:
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT status FROM orders WHERE id = %s AND user_id = %s FOR UPDATE",
                    (order_id, current_user["user_id"]),
                )
                row = cursor.fetchone()
                if row is None:
                    raise HTTPException(status_code=404, detail="订单不存在")
                if row[0] != "pending":
                    raise HTTPException(status_code=409, detail="只有待处理订单可以取消")

                cursor.execute(
                    """
                    UPDATE orders
                    SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s AND user_id = %s AND status = 'pending'
                    RETURNING id, status
                    """,
                    (order_id, current_user["user_id"]),
                )
                updated_row = cursor.fetchone()
        return {"id": updated_row[0], "status": updated_row[1], "message": "订单已取消"}
    finally:
        conn.close()


def get_admin_orders_service(status: OrderStatus | None = None) -> list[dict]:
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                params: tuple[object, ...] = ()
                status_clause = ""
                if status is not None:
                    status_clause = "WHERE o.status = %s"
                    params = (status,)

                cursor.execute(
                    f"""
                    SELECT o.id, o.user_id, o.status, o.created_at, o.updated_at
                    FROM orders o
                    {status_clause}
                    ORDER BY o.id DESC
                    """,
                    params,
                )
                order_rows = cursor.fetchall()
                if not order_rows:
                    return []

                order_ids = [row[0] for row in order_rows]
                cursor.execute(
                    """
                    SELECT oi.id, oi.order_id, oi.recipe_id, r.name,
                           oi.quantity, oi.price, r.image_url
                    FROM order_items oi
                    JOIN recipes r ON r.id = oi.recipe_id
                    WHERE oi.order_id = ANY(%s)
                    ORDER BY oi.order_id, oi.id
                    """,
                    (order_ids,),
                )
                item_rows_by_order: dict[int, list[tuple]] = {}
                for row in cursor.fetchall():
                    item_rows_by_order.setdefault(row[1], []).append(
                        (row[0], row[2], row[3], row[4], row[5], row[6])
                    )
        return [
            _serialize_order(order_row, item_rows_by_order.get(order_row[0], []))
            for order_row in order_rows
        ]
    finally:
        conn.close()


def get_admin_order_service(order_id: int) -> dict:
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, user_id, status, created_at, updated_at
                    FROM orders
                    WHERE id = %s
                    """,
                    (order_id,),
                )
                order_row = cursor.fetchone()
                if order_row is None:
                    raise HTTPException(status_code=404, detail="订单不存在")

                cursor.execute(
                    """
                    SELECT oi.id, oi.recipe_id, r.name, oi.quantity, oi.price, r.image_url
                    FROM order_items oi
                    JOIN recipes r ON r.id = oi.recipe_id
                    WHERE oi.order_id = %s
                    ORDER BY oi.id ASC
                    """,
                    (order_id,),
                )
                item_rows = cursor.fetchall()
        return _serialize_order(order_row, item_rows)
    finally:
        conn.close()


def update_admin_order_status_service(
    order_id: int,
    status_update: AdminOrderStatusUpdate,
) -> dict:
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT status FROM orders WHERE id = %s FOR UPDATE",
                    (order_id,),
                )
                row = cursor.fetchone()
                if row is None:
                    raise HTTPException(status_code=404, detail="订单不存在")

                current_status = row[0]
                next_status = status_update.status
                if current_status == next_status:
                    pass
                elif current_status != "pending":
                    raise HTTPException(
                        status_code=409,
                        detail="已完成或已取消订单不能再次修改状态",
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE orders
                        SET status = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s AND status = 'pending'
                        RETURNING id
                        """,
                        (next_status, order_id),
                    )
                    if cursor.fetchone() is None:
                        raise HTTPException(status_code=409, detail="订单状态已发生变化")
        return get_admin_order_service(order_id)
    finally:
        conn.close()
