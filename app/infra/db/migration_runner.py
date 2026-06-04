from pathlib import Path

SCHEMA_DIR = Path("app/infra/db/schemas")
MIGRATIONS_DIR = Path("app/infra/db/migrations")


async def run_base_schema(conn):
    order = [
        "types.sql",
        "notifications.sql",
        "delivery_attempts.sql",
        "idempotency_keys.sql",
    ]
    for name in order:
        file = SCHEMA_DIR / name
        await conn.execute(file.read_text())


async def run_migrations(conn):
    # 1. Create schema_version table
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_version (
            version INT PRIMARY KEY
        );
        """
    )

    # 2. Check current version
    version = await conn.fetchval("SELECT version FROM schema_version LIMIT 1;")

    # 3. Fresh DB → run base schema
    if version is None:
        await run_base_schema(conn)
        await conn.execute("INSERT INTO schema_version (version) VALUES (1);")
        version = 1

    # 4. Apply migrations
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))

    for file in migration_files:
        migration_version = int(file.name.split("_")[0])

        if migration_version > version:
            async with conn.transaction():
                await conn.execute(file.read_text())

                await conn.execute(
                    "UPDATE schema_version SET version = $1;", migration_version
                )

            version = migration_version
