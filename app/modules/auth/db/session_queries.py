async def create_session(
    conn,
    user_id,
    refresh_token_hash,
    expires_at,
):
    query = """
    INSERT INTO sessions (
      user_id,
      refresh_token_hash,
      expires_at
    )
    VALUES ($1, $2, $3)
    RETURNING *;
    """

    row = await conn.fetchrow(
        query,
        user_id,
        refresh_token_hash,
        expires_at,
    )

    if row is None:
        raise RuntimeError(
            "Insert failed: no row returned",
        )

    return dict(row)


async def get_session_by_refresh_token_hash(
    conn,
    refresh_token_hash: str,
):
    query = """
    SELECT *
    FROM sessions
    WHERE refresh_token_hash = $1
    AND revoked_at IS NULL;
    """

    row = await conn.fetchrow(query, refresh_token_hash)

    return dict(row) if row else None


async def get_session_by_id(conn, session_id):
    query = """
    SELECT *
    FROM sessions
    WHERE id = $1
    AND revoked_at IS NULL;
    """

    row = await conn.fetchrow(query, session_id)

    return dict(row) if row else None


async def rotate_session_refresh_token(
    conn,
    session_id,
    refresh_token_hash,
    expires_at,
):
    query = """
    UPDATE sessions
    SET refresh_token_hash = $2,
        expires_at = $3
    WHERE id = $1
    AND revoked_at IS NULL
    RETURNING *;
    """

    row = await conn.fetchrow(
        query,
        session_id,
        refresh_token_hash,
        expires_at,
    )

    return dict(row) if row else None


async def revoke_session(conn, session_id):
    query = """
    UPDATE sessions
    SET revoked_at = now()
    WHERE id = $1
    AND revoked_at IS NULL
    RETURNING *;
    """

    row = await conn.fetchrow(query, session_id)

    return dict(row) if row else None


async def revoke_all_user_sessions(conn, user_id):
    query = """
    UPDATE sessions
    SET revoked_at = NOW()
    WHERE user_id = $1
    AND revoked_at IS NULL;
    """

    await conn.execute(
        query,
        user_id,
    )
