from __future__ import annotations

import argparse
import hashlib
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from app.db.database import get_connection


MIGRATIONS_DIR = Path(__file__).with_name("migrations")
MIGRATION_PATTERN = re.compile(r"^(V\d+)__[^/]+\.sql$")
LOCK_KEY = "fyallstack:database:migrations"


@dataclass(frozen=True)
class Migration:
    version: str
    path: Path
    sql: str
    checksum: str


def load_migrations() -> list[Migration]:
    migrations: list[Migration] = []
    seen_versions: set[str] = set()
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        match = MIGRATION_PATTERN.match(path.name)
        if match is None:
            raise RuntimeError(f"迁移文件名无效: {path.name}")
        version = match.group(1)
        if version in seen_versions:
            raise RuntimeError(f"迁移版本重复: {version}")
        seen_versions.add(version)
        sql_bytes = path.read_bytes()
        migrations.append(
            Migration(
                version=version,
                path=path,
                sql=sql_bytes.decode("utf-8"),
                checksum=hashlib.sha256(sql_bytes).hexdigest(),
            )
        )
    return sorted(migrations, key=lambda item: int(item.version[1:]))


def _ensure_migration_table(conn) -> None:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(100) PRIMARY KEY,
                checksum CHAR(64) NOT NULL,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    conn.commit()


def _load_applied(conn) -> dict[str, str]:
    with conn.cursor() as cursor:
        cursor.execute("SELECT version, checksum FROM schema_migrations")
        return {version: checksum for version, checksum in cursor.fetchall()}


def _validate_checksums(
    migrations: list[Migration],
    applied: dict[str, str],
) -> None:
    migration_by_version = {migration.version: migration for migration in migrations}
    for version, checksum in applied.items():
        migration = migration_by_version.get(version)
        if migration is None:
            raise RuntimeError(f"数据库记录了代码中不存在的迁移版本: {version}")
        if checksum != migration.checksum:
            raise RuntimeError(f"已执行迁移 checksum 不匹配: {version}")


def _verify_baseline(cursor) -> None:
    required_columns = {
        "users": {"id", "username", "password_hash", "role", "created_at"},
        "recipe_categories": {"id", "name", "created_at"},
        "recipes": {
            "id", "name", "description", "price", "image_url", "category_id",
            "status", "created_at", "updated_at",
        },
        "orders": {"id", "user_id", "status", "created_at", "updated_at"},
        "order_items": {"id", "order_id", "recipe_id", "quantity", "price"},
    }
    for table, expected_columns in required_columns.items():
        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            """,
            (table,),
        )
        actual_columns = {row[0] for row in cursor.fetchall()}
        missing = expected_columns - actual_columns
        if missing:
            raise RuntimeError(
                f"V001 执行后 {table} 缺少字段: {', '.join(sorted(missing))}"
            )

    cursor.execute(
        """
        SELECT conname
        FROM pg_constraint
        WHERE conrelid IN (
            'public.users'::regclass,
            'public.recipes'::regclass,
            'public.orders'::regclass
        )
        """
    )
    constraint_names = {row[0] for row in cursor.fetchall()}
    required_constraints = {
        "users_role_check",
        "recipes_status_check",
        "orders_status_check",
    }
    missing_constraints = required_constraints - constraint_names
    if missing_constraints:
        raise RuntimeError(
            "V001 执行后缺少约束: " + ", ".join(sorted(missing_constraints))
        )

    cursor.execute(
        """
        SELECT indexname
        FROM pg_indexes
        WHERE schemaname = 'public'
          AND indexname IN (
              'recipes_category_status_idx',
              'orders_user_id_created_at_idx',
              'order_items_order_id_idx'
          )
        """
    )
    actual_indexes = {row[0] for row in cursor.fetchall()}
    required_indexes = {
        "recipes_category_status_idx",
        "orders_user_id_created_at_idx",
        "order_items_order_id_idx",
    }
    missing_indexes = required_indexes - actual_indexes
    if missing_indexes:
        raise RuntimeError("V001 执行后缺少索引: " + ", ".join(sorted(missing_indexes)))

    cursor.execute("SELECT COUNT(*) FROM users WHERE role IS NULL")
    if cursor.fetchone()[0] != 0:
        raise RuntimeError("V001 执行后 users.role 仍存在 NULL")


def _with_advisory_lock(conn) -> None:
    with conn.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_lock(hashtextextended(%s, 0))", (LOCK_KEY,))


def _release_advisory_lock(conn) -> None:
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT pg_advisory_unlock(hashtextextended(%s, 0))",
            (LOCK_KEY,),
        )


def migrate() -> int:
    migrations = load_migrations()
    conn = get_connection()
    lock_acquired = False
    try:
        _with_advisory_lock(conn)
        lock_acquired = True
        _ensure_migration_table(conn)
        applied = _load_applied(conn)
        # psycopg starts an implicit transaction for the SELECT above. End it
        # so each migration below runs in its own top-level transaction.
        conn.commit()
        _validate_checksums(migrations, applied)

        pending = [migration for migration in migrations if migration.version not in applied]
        if not pending:
            print("database migrations: up to date")
            return 0

        for migration in pending:
            print(f"applying {migration.version}: {migration.path.name}")
            with conn.transaction():
                with conn.cursor() as cursor:
                    cursor.execute(migration.sql)
                    if migration.version == "V001":
                        _verify_baseline(cursor)
                    cursor.execute(
                        """
                        INSERT INTO schema_migrations (version, checksum)
                        VALUES (%s, %s)
                        """,
                        (migration.version, migration.checksum),
                    )
            print(f"applied {migration.version}")
        return 0
    finally:
        if lock_acquired:
            _release_advisory_lock(conn)
        conn.close()


def status() -> int:
    migrations = load_migrations()
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT to_regclass('public.schema_migrations') IS NOT NULL
                """
            )
            initialized = cursor.fetchone()[0]
        if not initialized:
            print("database migrations: not initialized")
            for migration in migrations:
                print(f"pending {migration.version}: {migration.path.name}")
            return 0

        applied = _load_applied(conn)
        _validate_checksums(migrations, applied)
        for migration in migrations:
            state = "applied" if migration.version in applied else "pending"
            print(f"{state} {migration.version}: {migration.path.name}")
        return 0
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run versioned PostgreSQL migrations")
    parser.add_argument(
        "command",
        nargs="?",
        choices=("run", "status"),
        default="run",
    )
    args = parser.parse_args()
    try:
        return status() if args.command == "status" else migrate()
    except Exception as exc:
        print(f"database migrations failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
