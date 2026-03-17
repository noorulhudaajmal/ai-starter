from .setup import get_connection


def get_categories():
    conn = get_connection()
    rows = conn.execute("SELECT id, name, slug, icon FROM categories ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_products(
    category_id: int | None = None,
    gender: str | None = None,
    age_group: str | None = None,
    season: str | None = None,
    min_stock: int = 1,
    search: str | None = None,
) -> list[dict]:
    conn = get_connection()

    sql = """
        SELECT p.*, c.name AS category_name, c.icon AS category_icon,
               COALESCE(i.quantity, 0) AS stock
        FROM products p
        LEFT JOIN categories c ON c.id = p.category_id
        LEFT JOIN inventory i ON i.product_id = p.id
        WHERE p.is_active = 1
          AND COALESCE(i.quantity, 0) >= :min_stock
    """
    params: dict = {"min_stock": min_stock}

    if category_id:
        sql += " AND p.category_id = :category_id"
        params["category_id"] = category_id
    if gender and gender != "All":
        sql += " AND (p.gender = :gender OR p.gender = 'Unisex')"
        params["gender"] = gender
    if age_group and age_group != "All":
        sql += " AND (p.age_group = :age_group OR p.age_group = 'All')"
        params["age_group"] = age_group
    if season and season != "All":
        sql += " AND (p.season = :season OR p.season = 'All')"
        params["season"] = season
    if search:
        sql += " AND (p.name LIKE :search OR p.tags LIKE :search OR p.brand LIKE :search)"
        params["search"] = f"%{search}%"

    sql += " ORDER BY p.name"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_product_by_id(product_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        """SELECT p.*, c.name AS category_name, COALESCE(i.quantity,0) AS stock
           FROM products p
           LEFT JOIN categories c ON c.id = p.category_id
           LEFT JOIN inventory i ON i.product_id = p.id
           WHERE p.id = ?""",
        (product_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_sales_stats(product_id: int) -> dict:
    conn = get_connection()
    row = conn.execute(
        """SELECT
               COUNT(*) AS total_transactions,
               COALESCE(SUM(quantity), 0) AS total_units_sold,
               COALESCE(SUM(quantity * unit_price), 0) AS total_revenue,
               COALESCE(AVG(unit_price), 0) AS avg_price
           FROM sales WHERE product_id = ?""",
        (product_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else {}


def save_campaign(data: dict) -> int:
    conn = get_connection()
    import json
    cur = conn.execute(
        """INSERT INTO campaigns
           (name, product_id, status, trend_summary, caption, tagline, quote, image_path, report_path, filters_json)
           VALUES (:name, :product_id, :status, :trend_summary, :caption, :tagline, :quote, :image_path, :report_path, :filters_json)""",
        {
            "name": data.get("name", "Untitled Campaign"),
            "product_id": data.get("product_id"),
            "status": data.get("status", "draft"),
            "trend_summary": data.get("trend_summary", ""),
            "caption": data.get("caption", ""),
            "tagline": data.get("tagline", ""),
            "quote": data.get("quote", ""),
            "image_path": data.get("image_path", ""),
            "report_path": data.get("report_path", ""),
            "filters_json": json.dumps(data.get("filters", {})),
        },
    )
    conn.commit()
    campaign_id = cur.lastrowid
    conn.close()
    return campaign_id


def get_campaigns(limit: int = 20) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT cam.*, p.name AS product_name, c.icon AS category_icon
           FROM campaigns cam
           LEFT JOIN products p ON p.id = cam.product_id
           LEFT JOIN categories c ON c.id = p.category_id
           ORDER BY cam.created_at DESC LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]