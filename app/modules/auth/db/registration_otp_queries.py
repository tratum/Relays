from datetime import datetime


async def create_registration_otp(
    conn,
    email: str,
    otp_hash: str,
    expires_at: datetime,
):
    query = """
    INSERT INTO registration_otp (
      email,
      otp_hash,
      expires_at
    )
    VALUES ($1, $2, $3)
    RETURNING *;
    """

    row = await conn.fetchrow(
        query,
        email,
        otp_hash,
        expires_at,
    )

    if row is None:
        raise RuntimeError("Insert failed: no row returned")

    return dict(row)


async def get_registration_otp_by_email(
    conn,
    email: str,
):
    query = """
    SELECT *
    FROM registration_otp
    WHERE email = $1;
    """

    row = await conn.fetchrow(query, email)

    return dict(row) if row else None


async def consume_registration_otp(
    conn,
    email: str,
):
    query = """
    UPDATE registration_otp
    SET consumed_at = NOW()
    WHERE email = $1
      AND consumed_at IS NULL
    RETURNING *;
    """

    row = await conn.fetchrow(query, email)

    return dict(row) if row else None


async def delete_registration_otp(
    conn,
    email: str,
):
    query = """
    DELETE FROM registration_otp
    WHERE email = $1;
    """

    await conn.execute(query, email)
