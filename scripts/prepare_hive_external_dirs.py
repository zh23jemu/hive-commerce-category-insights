"""准备 Hive 外部表目录。

Hive 外部表的 LOCATION 指向目录而不是单个 CSV 文件。该脚本会在本地
`data/raw/olist/` 下为每张 ODS 表创建稳定目录，并复制对应 CSV 为 `data.csv`。
项目目录会挂载到 Hive 容器的 `/workspace`，因此 Hive 可以直接读取这些目录。
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_DIR = PROJECT_ROOT / "data" / "raw" / "olist"

CSV_TO_ODS_DIR = {
    "olist_orders_dataset.csv": "ods_orders",
    "olist_order_items_dataset.csv": "ods_order_items",
    "olist_products_dataset.csv": "ods_products",
    "product_category_name_translation.csv": "ods_product_category_translation",
    "olist_customers_dataset.csv": "ods_customers",
    "olist_sellers_dataset.csv": "ods_sellers",
    "olist_order_payments_dataset.csv": "ods_order_payments",
    "olist_order_reviews_dataset.csv": "ods_order_reviews",
    "olist_geolocation_dataset.csv": "ods_geolocation",
}


def parse_args() -> argparse.Namespace:
    """解析 Olist 原始 CSV 目录。"""
    parser = argparse.ArgumentParser(description="准备 Hive 外部表目录")
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR, help="Olist 原始 CSV 目录")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    for csv_name, ods_dir_name in CSV_TO_ODS_DIR.items():
        source = args.raw_dir / csv_name
        if not source.exists():
            raise FileNotFoundError(f"缺少原始 CSV，请先执行 prepare_data.py：{source}")

        target_dir = args.raw_dir / ods_dir_name
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / "data.csv"
        shutil.copy2(source, target)
        print(f"已准备 Hive 外部表目录：{target}")

    print("Hive 外部表目录准备完成。")


if __name__ == "__main__":
    main()
