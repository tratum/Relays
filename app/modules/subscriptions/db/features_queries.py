async def get_plan_features(
    conn,
    plan_id: int,
):
    query = """
    SELECT
      f.id,
      f.feature_key,
      f.display_name,
      f.description
    FROM plan_features pf
    JOIN features f
      ON f.id = pf.feature_id
    WHERE pf.plan_id = $1
      AND f.is_active = TRUE
    ORDER BY f.id;
    """

    rows = await conn.fetch(query, plan_id)

    return [dict(row) for row in rows]
