"""使用 Pandas 生成本地 ADS 演示结果。

该脚本不替代正式的 Spark + Hive 链路，只用于在 Windows 本机没有配置 Hadoop
`winutils.exe` 或 Docker 环境尚未启动时，快速生成与 ADS 表同结构的 CSV，
方便验证 Streamlit 页面和课程演示图表。
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_DIR = PROJECT_ROOT / "data" / "raw" / "olist"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "exports" / "ads_category_sales_ratio.csv"


def parse_args() -> argparse.Namespace:
    """解析 Olist 原始数据目录和 ADS 结果输出路径。"""
    parser = argparse.ArgumentParser(description="用 Pandas 生成本地 ADS 类目销售占比结果")
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR, help="Olist 原始 CSV 目录")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="ADS 结果 CSV 输出路径")
    return parser.parse_args()


def read_required_csv(raw_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """读取计算类目销售占比所需的三张核心表。"""
    order_items = pd.read_csv(raw_dir / "olist_order_items_dataset.csv")
    products = pd.read_csv(raw_dir / "olist_products_dataset.csv")
    translations = pd.read_csv(raw_dir / "product_category_name_translation.csv")
    return order_items, products, translations


def build_ads(raw_dir: Path) -> pd.DataFrame:
    """按 Hive ADS 表口径生成类目销售占比结果。"""
    order_items, products, translations = read_required_csv(raw_dir)

    detail = (
        order_items.merge(products[["product_id", "product_category_name"]], on="product_id", how="left")
        .merge(translations, on="product_category_name", how="left")
        .dropna(subset=["product_category_name", "price"])
    )
    detail["category_name_en"] = detail["product_category_name_english"].fillna(detail["product_category_name"])
    detail["sales_quantity"] = 1
    detail["sales_amount"] = detail["price"].astype(float)
    detail["sales_amount_with_freight"] = detail["price"].astype(float) + detail["freight_value"].fillna(0).astype(float)

    summary = (
        detail.groupby("category_name_en", as_index=False)
        .agg(
            sales_quantity=("sales_quantity", "sum"),
            sales_amount=("sales_amount", "sum"),
            sales_amount_with_freight=("sales_amount_with_freight", "sum"),
            order_count=("order_id", "nunique"),
            product_count=("product_id", "nunique"),
        )
        .sort_values("sales_amount", ascending=False)
        .reset_index(drop=True)
    )

    total_quantity = summary["sales_quantity"].sum()
    total_sales_amount = summary["sales_amount"].sum()
    summary["quantity_ratio"] = (summary["sales_quantity"] / total_quantity * 100).round(2)
    summary["sales_amount_ratio"] = (summary["sales_amount"] / total_sales_amount * 100).round(2)
    summary["sales_amount"] = summary["sales_amount"].round(2)
    summary["sales_amount_with_freight"] = summary["sales_amount_with_freight"].round(2)
    summary["sales_amount_rank"] = range(1, len(summary) + 1)
    summary["category_type"] = summary["sales_amount_rank"].map(classify_category)
    return summary


def classify_category(rank: int) -> str:
    """按照销售额排名划分类目类型，与 Hive ADS SQL 保持一致。"""
    if rank <= 10:
        return "核心类目"
    if rank <= 30:
        return "辅助类目"
    return "弱势类目"


def main() -> None:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    ads = build_ads(args.raw_dir)
    ads.to_csv(args.output, index=False, encoding="utf-8-sig")
    print(f"本地 ADS 演示结果已生成：{args.output}")


if __name__ == "__main__":
    main()

