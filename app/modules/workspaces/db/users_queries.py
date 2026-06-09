async def create_user(
    conn,
    name: str,
    email: str,
):
    query = """
    INSERT INTO users (name, email)
    VALUES ($1, $2)
    RETURNING
      id,
      email,
      name,
      is_verified,
      created_at;
    """

    row = await conn.fetchrow(
        query,
        name,
        email,
    )

    if row is None:
        raise RuntimeError("Insert failed: no row returned")

    return dict(row)


async def update_user_name(
    conn,
    user_id,
    name: str,
):
    query = """
    UPDATE users
    SET
      name = $2,
      updated_at = now()
    WHERE id = $1
    RETURNING
      id,
      email,
      name,
      is_verified,
      created_at;
    """

    row = await conn.fetchrow(
        query,
        user_id,
        name,
    )

    return dict(row) if row else None


async def get_user_by_id(
    conn,
    user_id,
):
    query = """
    SELECT
      id,
      email,
      name,
      is_verified,
      created_at
    FROM users
    WHERE id = $1;
    """

    row = await conn.fetchrow(query, user_id)

    return dict(row) if row else None


async def get_user_by_email(
    conn,
    email: str,
):
    query = """
    SELECT
      id,
      email,
      name,
      is_verified,
      created_at
    FROM users
    WHERE email = $1;
    """

    row = await conn.fetchrow(query, email)

    return dict(row) if row else None
