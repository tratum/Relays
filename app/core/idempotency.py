async def insert_idem_keys(
    conn,
    idem_key: str,
    request_hash,
    api_key_id: str,
    method: str,
    path: str,
):
    query = """
    INSERT INTO idempotency_keys (
      idempotency_key,
      request_hash,
      api_key_id,
      method,
      path,
      status,
      expires_at
    )
    VALUES ($1, $2, $3, $4, $5, 'processing', now() + interval '24 hours')
    ON CONFLICT (idempotency_key, api_key_id, method, path)
    DO NOTHING
    RETURNING *;
    """
    return await conn.fetchrow(
        query,
        idem_key,
        request_hash,
        api_key_id,
        method,
        path,
    )


async def get_idem_keys(
    conn,
    idem_key: str,
    api_key_id: str,
    method: str,
    path: str,
):
    query = """
    SELECT * FROM idempotency_keys
    WHERE idempotency_key = $1
    AND api_key_id = $2
    AND method = $3
    AND path = $4;
    """

    return await conn.fetchrow(
        query,
        idem_key,
        api_key_id,
        method,
        path,
    )


async def complete_idempotency(conn, idem_id: int, notification_id: int):
    query = """
    UPDATE idempotency_keys
    SET STATUS = 'completed',
        notification_id =  $2
    WHERE id = $1;
    """

    await conn.execute(
        query,
        idem_id,
        notification_id,
    )
