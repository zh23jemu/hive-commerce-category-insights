"""使用 PySpark 生成电商类目销售明细宽表。

脚本会读取 Olist 原始 CSV，关联订单明细、订单、商品和类目翻译表，生成后续
Hive 聚合分析需要的 DWD 明细数据。默认输出到本地 `data/processed/dwd`，
在 Docker 环境中也可以通过参数改为 HDFS 路径。
"""

from __future__ import annotations

import argparse
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_DIR = PROJECT_ROOT / "data" / "raw" / "olist"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "dwd" / "order_category_sales_detail"


def parse_args() -> argparse.Namespace:
    """解析输入输出路径，便于本地模式和 Docker/HDFS 模式复用同一份代码。"""
    parser = argparse.ArgumentParser(description="清洗 Olist 类目销售明细数据")
    parser.add_argument("--raw-dir", default=str(DEFAULT_RAW_DIR), help="Olist 原始 CSV 目录")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_DIR), help="DWD 明细数据输出路径")
    parser.add_argument("--master", default="local[*]", help="Spark master，例如 local[*] 或 spark://spark-master:7077")
    parser.add_argument("--format", default="parquet", choices=["parquet", "csv"], help="输出格式")
    return parser.parse_args()


def build_spark(master: str) -> SparkSession:
    """创建 SparkSession，并开启 Hive 支持以便后续扩展写入 Hive 表。"""
    return (
        SparkSession.builder.appName("olist-category-sales-clean")
        .master(master)
        .config("spark.sql.session.timeZone", "Asia/Shanghai")
        .enableHiveSupport()
        .getOrCreate()
    )


def read_csv(spark: SparkSession, raw_dir: str, filename: str):
    """按 Olist CSV 的常规格式读取数据，统一启用表头和类型推断。"""
    return (
        spark.read.option("header", "true")
        .option("inferSchema", "true")
        .option("multiLine", "true")
        .option("escape", '"')
        .csv(f"{raw_dir.rstrip('/')}/{filename}")
    )


def create_detail(raw_dir: str, spark: SparkSession):
    """关联核心表并计算销售明细字段。

    Olist 的订单明细表每一行代表一个订单中的一个商品条目，因此项目默认把每行
    计为 1 件销量。销售额主口径使用商品价格 `price`，运费 `freight_value`
    作为扩展指标保留，方便报告中解释不同口径。
    """
    order_items = read_csv(spark, raw_dir, "olist_order_items_dataset.csv")
    orders = read_csv(spark, raw_dir, "olist_orders_dataset.csv")
    products = read_csv(spark, raw_dir, "olist_products_dataset.csv")
    translations = read_csv(spark, raw_dir, "product_category_name_translation.csv")

    detail = (
        order_items.alias("oi")
        .join(orders.alias("o"), F.col("oi.order_id") == F.col("o.order_id"), "left")
        .join(products.alias("p"), F.col("oi.product_id") == F.col("p.product_id"), "left")
        .join(
            translations.alias("t"),
            F.col("p.product_category_name") == F.col("t.product_category_name"),
            "left",
        )
        .select(
            F.col("oi.order_id").alias("order_id"),
            F.col("oi.order_item_id").cast("int").alias("order_item_id"),
            F.col("oi.product_id").alias("product_id"),
            F.col("oi.seller_id").alias("seller_id"),
            F.col("p.product_category_name").alias("category_name_pt"),
            F.coalesce(F.col("t.product_category_name_english"), F.col("p.product_category_name")).alias(
                "category_name_en"
            ),
            F.col("o.order_status").alias("order_status"),
            F.to_timestamp("o.order_purchase_timestamp").alias("order_purchase_ts"),
            F.col("oi.price").cast("double").alias("price"),
            F.col("oi.freight_value").cast("double").alias("freight_value"),
            F.lit(1).cast("int").alias("quantity"),
        )
        .where(F.col("category_name_en").isNotNull())
        .where(F.col("price").isNotNull())
        .withColumn("sales_amount", F.col("price"))
        .withColumn("sales_amount_with_freight", F.col("price") + F.coalesce(F.col("freight_value"), F.lit(0.0)))
        .withColumn("order_date", F.to_date("order_purchase_ts"))
    )

    return detail


def write_detail(detail, output: str, output_format: str) -> None:
    """写出明细宽表，默认使用 Parquet 便于 Hive/Spark 后续高效读取。"""
    writer = detail.repartition(1).write.mode("overwrite")
    if output_format == "csv":
        writer.option("header", "true").csv(output)
    else:
        writer.parquet(output)


def main() -> None:
    args = parse_args()
    spark = build_spark(args.master)
    try:
        detail = create_detail(args.raw_dir, spark)
        write_detail(detail, args.output, args.format)
        print(f"DWD 类目销售明细已生成：{args.output}")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()

