async def insert_billing_period(
    conn,
    subscription_id,
    period_start,
):
    query = """
    INSERT INTO billing_periods (
      subscription_id,
      period_start,
      period_end
    )
    VALUES (
      $1,
      $2,
      $2 + INTERVAL '1 month'
    )
    RETURNING *;
    """

    row = await conn.fetchrow(
        query,
        subscription_id,
        period_start,
    )

    if row is None:
        raise RuntimeError("Insert failed: no row returned")

    return dict(row)


async def get_current_billing_period(conn, subscription_id):
    query = """
    SELECT *
    FROM billing_periods
    WHERE subscription_id = $1
      AND period_start <= NOW()
      AND period_end > NOW();
    """

    row = await conn.fetchrow(query, subscription_id)

    return dict(row) if row else None
