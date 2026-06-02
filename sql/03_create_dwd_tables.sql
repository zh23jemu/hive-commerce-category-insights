USE olist_category_insights;

DROP TABLE IF EXISTS dwd_order_category_sales_detail;

CREATE TABLE dwd_order_category_sales_detail
STORED AS ORC
AS
SELECT
  oi.order_id,
  oi.order_item_id,
  oi.product_id,
  oi.seller_id,
  p.product_category_name AS category_name_pt,
  COALESCE(t.product_category_name_english, p.product_category_name) AS category_name_en,
  o.order_status,
  CAST(o.order_purchase_timestamp AS TIMESTAMP) AS order_purchase_ts,
  CAST(oi.price AS DOUBLE) AS price,
  CAST(oi.freight_value AS DOUBLE) AS freight_value,
  1 AS quantity,
  CAST(oi.price AS DOUBLE) AS sales_amount,
  CAST(oi.price AS DOUBLE) + COALESCE(CAST(oi.freight_value AS DOUBLE), 0.0) AS sales_amount_with_freight
FROM ods_order_items oi
LEFT JOIN ods_orders o
  ON oi.order_id = o.order_id
LEFT JOIN ods_products p
  ON oi.product_id = p.product_id
LEFT JOIN ods_product_category_translation t
  ON p.product_category_name = t.product_category_name
WHERE p.product_category_name IS NOT NULL
  AND oi.price IS NOT NULL;

