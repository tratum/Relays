async def insert_subscription(
    conn,
    workspace_id,
    plan_id,
):
    query = """
    INSERT INTO subscriptions (
      workspace_id,
      plan_id
    )
    VALUES ($1, $2)
    RETURNING *;
    """

    row = await conn.fetchrow(
        query,
        workspace_id,
        plan_id,
    )

    if row is None:
        raise RuntimeError("Insert failed: no row returned")

    return dict(row)


async def get_subscription(conn, subscription_id):
    query = """
    SELECT *
    FROM subscriptions
    WHERE id = $1;
    """

    row = await conn.fetchrow(query, subscription_id)

    return dict(row) if row else None


async def get_subscription_by_workspace(conn, workspace_id):
    query = """
    SELECT *
    FROM subscriptions
    WHERE workspace_id = $1;
    """

    row = await conn.fetchrow(query, workspace_id)

    return dict(row) if row else None


async def update_subscription_plan(conn, subscription_id, plan_id):
    query = """
    UPDATE subscriptions
    SET
      plan_id = $2,
      updated_at = now()
    WHERE id = $1
    AND status = 'active'
    RETURNING *;
    """

    row = await conn.fetchrow(
        query,
        subscription_id,
        plan_id,
    )

    return dict(row) if row else None


async def cancel_subscription(conn, subscription_id):
    query = """
    UPDATE subscriptions
    SET
      status = 'cancelled',
      cancelled_at = now(),
      updated_at = now()
    WHERE id = $1
    AND status = 'active'
    RETURNING *;
    """

    row = await conn.fetchrow(query, subscription_id)

    return dict(row) if row else None
