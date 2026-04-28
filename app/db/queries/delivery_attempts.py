async def succesfull_delivery_attempt(
    conn,
    notification_id,
    attempt_number,
    provider_response=None,
):
    query = """
    INSERT INTO delivery_attempts (
        id,
        notification_id,
        attempt_number,
        status,
        provider_response
    )
    VALUES (gen_random_uuid(), $1, $2, 'success', $3::jsonb);
    """
    await conn.execute(
        query,
        notification_id,
        attempt_number,
        provider_response,
    )


async def failed_delivery_attempt(
    conn, notification_id, attempt_number, status, error_message
):
    query = """
    INSERT INTO delivery_attempts (
      id,
      notification_id,
      attempt_number,
      status,
      error_message
    )
    VALUES (gen_random_uuid(), $1, $2, $3, $4)
    """
    await conn.execute(
        query, notification_id, attempt_number, status, error_message
    )
