USE olist_category_insights;

DROP TABLE IF EXISTS dws_category_sales_summary;

CREATE TABLE dws_category_sales_summary
STORED AS ORC
AS
SELECT
  category_name_en,
  COUNT(1) AS sales_quantity,
  ROUND(SUM(sales_amount), 2) AS sales_amount,
  ROUND(SUM(sales_amount_with_freight), 2) AS sales_amount_with_freight,
  COUNT(DISTINCT order_id) AS order_count,
  COUNT(DISTINCT product_id) AS product_count
FROM dwd_order_category_sales_detail
GROUP BY category_name_en;

DROP TABLE IF EXISTS ads_category_sales_ratio;

CREATE TABLE ads_category_sales_ratio
STORED AS ORC
AS
WITH total_value AS (
  SELECT
    SUM(sales_quantity) AS total_quantity,
    SUM(sales_amount) AS total_sales_amount
  FROM dws_category_sales_summary
),
ranked AS (
  SELECT
    s.category_name_en,
    s.sales_quantity,
    s.sales_amount,
    s.sales_amount_with_freight,
    s.order_count,
    s.product_count,
    ROUND(s.sales_quantity / t.total_quantity * 100, 2) AS quantity_ratio,
    ROUND(s.sales_amount / t.total_sales_amount * 100, 2) AS sales_amount_ratio,
    ROW_NUMBER() OVER (ORDER BY s.sales_amount DESC) AS sales_amount_rank
  FROM dws_category_sales_summary s
  CROSS JOIN total_value t
)
SELECT
  category_name_en,
  sales_quantity,
  sales_amount,
  sales_amount_with_freight,
  order_count,
  product_count,
  quantity_ratio,
  sales_amount_ratio,
  sales_amount_rank,
  CASE
    WHEN sales_amount_rank <= 10 THEN '核心类目'
    WHEN sales_amount_rank <= 30 THEN '辅助类目'
    ELSE '弱势类目'
  END AS category_type
FROM ranked;

