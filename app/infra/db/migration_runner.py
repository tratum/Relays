from pathlib import Path

SCHEMA_DIR = Path("app/infra/db/schemas")
MIGRATIONS_DIR = Path("app/infra/db/migrations")


async def run_base_schema(conn):
    # Execute base schema files for a fresh database
    schema_files = sorted(SCHEMA_DIR.rglob("*.sql"))

    for file in schema_files:
        await conn.execute(file.read_text())


async def run_migrations(conn):
    # 1. Create schema_version table if it doesn't exist
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )

    # 2. Get latest applied migration version
    current_version = await conn.fetchval(
        """
        SELECT MAX(version)
        FROM schema_version;
        """
    )

    # 3. Fresh database → run base schema
    if current_version is None:
        await run_base_schema(conn)

        # Record base schema initialization
        await conn.execute(
            """
            INSERT INTO schema_version(version)
            VALUES (0);
            """
        )

        current_version = 0

    # 4. Discover migration files
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))

    # 5. Apply pending migrations
    for file in migration_files:
        migration_version = int(file.stem.split("_")[0])

        if migration_version > current_version:
            async with conn.transaction():
                # Execute migration
                await conn.execute(file.read_text())

                # Record migration version
                await conn.execute(
                    """
                    INSERT INTO schema_version(version)
                    VALUES ($1);
                    """,
                    migration_version,
                )

            current_version = migration_version
