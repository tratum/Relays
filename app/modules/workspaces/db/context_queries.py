from uuid import UUID


async def get_workspace_context(
    conn,
    user_id: UUID,
):
    query = """
    SELECT
      u.id AS user_id,
      u.email,
      u.is_verified,
      wm.workspace_id,
      wm.role
    FROM users u
    INNER JOIN workspace_members wm
      ON wm.user_id = u.id
    WHERE u.id = $1;
    """

    row = await conn.fetchrow(query, user_id)

    return dict(row) if row else None


async def get_current_user_context(
    conn,
    user_id: UUID,
):
    query = """
    SELECT
      u.id AS user_id,
      u.name,
      u.email,
      w.id AS workspace_id,
      w.name AS workspace_name
    FROM users u
    INNER JOIN workspace_members wm
      ON wm.user_id = u.id
    INNER JOIN workspaces w
      ON w.id = wm.workspace_id
    WHERE u.id = $1;
    """

    row = await conn.fetchrow(query, user_id)

    return dict(row) if row else None
