from pathlib import Path

SCHEMA_DIR = Path("app/infra/db/schemas")
MIGRATIONS_DIR = Path("app/infra/db/migrations")

SCHEMA_PHASES = (
    "00-types",
    "01-tables",
    "02-constraints",
    "03-indexes",
    # "04-views", ## Currently Unused and Empty
)


async def run_base_schema(conn):
    """Execute the canonical schema for a fresh database."""

    for phase in SCHEMA_PHASES:
        phase_dir = SCHEMA_DIR / phase

        if not phase_dir.exists():
            continue

        for file in sorted(phase_dir.rglob("*.sql")):
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

    # 3. Fresh database → run canonical schema
    if current_version is None:
        async with conn.transaction():
            await run_base_schema(conn)

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

        if migration_version <= current_version:
            continue

        async with conn.transaction():
            await conn.execute(file.read_text())

            await conn.execute(
                """
                INSERT INTO schema_version(version)
                VALUES ($1);
                """,
                migration_version,
            )

        current_version = migration_version
