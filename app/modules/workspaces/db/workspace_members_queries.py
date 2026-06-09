async def create_workspace_member(
    conn,
    workspace_id,
    user_id,
    role,
):
    query = """
    INSERT INTO workspace_members (
        workspace_id,
        user_id,
        role
    )
    VALUES ($1, $2, $3)
    RETURNING
        workspace_id,
        user_id,
        role,
        joined_at;
    """

    row = await conn.fetchrow(
        query,
        workspace_id,
        user_id,
        role,
    )

    if row is None:
        raise RuntimeError("Insert failed: no row returned")

    return dict(row)


async def get_workspace_member(
    conn,
    workspace_id,
    user_id,
):
    query = """
    SELECT
      workspace_id,
      user_id,
      role,
      joined_at
    FROM workspace_members
    WHERE workspace_id = $1
      AND user_id = $2;
    """

    row = await conn.fetchrow(
        query,
        workspace_id,
        user_id,
    )

    return dict(row) if row else None


async def get_workspace_members(
    conn,
    workspace_id,
):
    query = """
    SELECT
      u.id AS user_id,
      u.email,
      u.name,
      wm.role
    FROM workspace_members wm
    INNER JOIN users u
      ON wm.user_id = u.id
    WHERE wm.workspace_id = $1
    ORDER BY
      CASE
          WHEN wm.role = 'OWNER' THEN 0
          ELSE 1
      END,
      u.name;
    """

    rows = await conn.fetch(
        query,
        workspace_id,
    )

    return [dict(row) for row in rows]
