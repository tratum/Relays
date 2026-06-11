async def create_workspace(
    conn,
    workspace_name: str,
    slug: str,
):
    query = """
    INSERT INTO workspaces (name, slug)
    VALUES ($1, $2)
    RETURNING id, name, slug, status, created_at;
    """

    row = await conn.fetchrow(query, workspace_name, slug)

    if row is None:
        raise RuntimeError("Insert failed: no row returned")

    return dict(row)


async def update_workspace_name(conn, workspace_id, workspace_name: str):
    query = """
    UPDATE workspaces
    SET name = $2,
        updated_at = now()
    WHERE id = $1
    RETURNING id, name, slug, status, created_at;
    """
    row = await conn.fetchrow(
        query,
        workspace_id,
        workspace_name,
    )

    return dict(row) if row else None


async def get_workspace(conn, workspace_id):
    row = await conn.fetchrow(
        "SELECT * FROM workspaces WHERE id = $1;",
        workspace_id,
    )
    return dict(row) if row else None


async def get_workspace_by_slug(conn, slug: str):
    row = await conn.fetchrow(
        "SELECT * FROM workspaces WHERE slug = $1;",
        slug,
    )
    return dict(row) if row else None
