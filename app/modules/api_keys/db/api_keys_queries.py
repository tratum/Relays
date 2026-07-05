from datetime import datetime
from uuid import UUID


async def create_api_key(
    conn,
    workspace_id: UUID,
    created_by: UUID,
    name: str,
    key_prefix: str,
    key_hash: str,
    expires_at: datetime | None = None,
):
    query = """
    INSERT INTO api_keys (
      workspace_id,
      created_by,
      name,
      key_prefix,
      key_hash,
      expires_at
    )
    VALUES ($1, $2, $3, $4, $5, $6)
    RETURNING
      id,
      workspace_id,
      name,
      key_prefix,
      status,
      expires_at,
      last_used_at,
      revoked_at,
      created_at,
      updated_at;
    """

    row = await conn.fetchrow(
        query,
        workspace_id,
        created_by,
        name,
        key_prefix,
        key_hash,
        expires_at,
    )

    if row is None:
        raise RuntimeError("Insert failed: no row returned")

    return dict(row)


async def get_api_key(
    conn,
    api_key_id: UUID,
):
    query = """
    SELECT
      id,
      workspace_id,
      name,
      key_prefix,
      status,
      expires_at,
      last_used_at,
      revoked_at,
      created_at,
      updated_at
    FROM api_keys
    WHERE id = $1;
    """

    row = await conn.fetchrow(
        query,
        api_key_id,
    )

    return dict(row) if row else None


async def get_api_key_by_id_and_workspace(
    conn,
    api_key_id: UUID,
    workspace_id: UUID,
):
    query = """
    SELECT
      id,
      workspace_id,
      name,
      key_prefix,
      status,
      expires_at,
      last_used_at,
      revoked_at,
      created_at,
      updated_at
    FROM api_keys
    WHERE id = $1
      AND workspace_id = $2;
    """

    row = await conn.fetchrow(
        query,
        api_key_id,
        workspace_id,
    )

    return dict(row) if row else None


async def get_api_key_by_prefix(
    conn,
    key_prefix: str,
):
    query = """
    SELECT
      id,
      workspace_id,
      key_hash,
      status,
      expires_at
    FROM api_keys
    WHERE key_prefix = $1;
    """

    row = await conn.fetchrow(
        query,
        key_prefix,
    )

    return dict(row) if row else None


async def list_workspace_api_keys(
    conn,
    workspace_id: UUID,
):
    query = """
    SELECT
      id,
      workspace_id,
      name,
      key_prefix,
      status,
      expires_at,
      last_used_at,
      revoked_at,
      created_at,
      updated_at
    FROM api_keys
    WHERE workspace_id = $1
    ORDER BY created_at DESC;
    """

    rows = await conn.fetch(
        query,
        workspace_id,
    )

    return [dict(row) for row in rows]


async def count_active_api_keys(
    conn,
    workspace_id: UUID,
):
    query = """
    SELECT COUNT(*)
    FROM api_keys
    WHERE workspace_id = $1
      AND status = 'active'
      AND (
        expires_at IS NULL
        OR expires_at > NOW()
      );
    """

    return await conn.fetchval(
        query,
        workspace_id,
    )


async def revoke_api_key(
    conn,
    api_key_id: UUID,
    workspace_id: UUID,
):
    query = """
    UPDATE api_keys
    SET
      status = 'revoked',
      revoked_at = NOW(),
      updated_at = NOW()
    WHERE id = $1
      AND workspace_id = $2
      AND status = 'active'
    RETURNING
      id,
      workspace_id,
      name,
      key_prefix,
      status,
      expires_at,
      last_used_at,
      revoked_at,
      created_at,
      updated_at;
    """

    row = await conn.fetchrow(
        query,
        api_key_id,
        workspace_id,
    )

    return dict(row) if row else None


async def update_api_key_last_used(
    conn,
    api_key_id: UUID,
):
    query = """
    UPDATE api_keys
    SET
      last_used_at = NOW(),
      updated_at = NOW()
    WHERE id = $1;
    """

    await conn.execute(
        query,
        api_key_id,
    )
