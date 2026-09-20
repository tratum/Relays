async def get_plan(
    conn,
    plan_id: int,
):
    query = """
    SELECT *
    FROM plans
    WHERE id = $1;
    """

    row = await conn.fetchrow(
        query,
        plan_id,
    )

    return dict(row) if row else None


async def list_active_plans(
    conn,
):
    query = """
    SELECT *
    FROM plans
    WHERE is_active = TRUE
    ORDER BY id;
    """

    rows = await conn.fetch(query)

    return [dict(row) for row in rows]