from datetime import datetime
from uuid import UUID


async def create_login_otp(
    conn,
    user_id: UUID,
    otp_hash: str,
    expires_at: datetime,
):
    query = """
    INSERT INTO login_otp (
      user_id,
      otp_hash,
      expires_at
    )
    VALUES ($1, $2, $3)
    RETURNING *;
    """

    row = await conn.fetchrow(query, user_id, otp_hash, expires_at)

    if row is None:
        raise RuntimeError("Insert failed: no row returned")

    return dict(row)


async def get_login_otp_by_user_id(conn, user_id: UUID):
    query = """
    SELECT *
    FROM login_otp
    WHERE user_id = $1;
    """

    row = await conn.fetchrow(query, user_id)
    return dict(row) if row else None


async def consume_login_otp(conn, user_id: UUID):
    query = """
    UPDATE login_otp
    SET consumed_at = NOW()
    WHERE user_id = $1
    AND consumed_at IS NULL
    RETURNING *;
    """

    row = await conn.fetchrow(query, user_id)
    return dict(row) if row else None


async def delete_login_otp(conn, user_id: UUID):
    query = """
    DELETE FROM login_otp
    WHERE user_id = $1;
    """

    await conn.execute(query, user_id)
