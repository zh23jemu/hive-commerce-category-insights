"""准备 Olist 原始数据。

该脚本只负责把已下载的 zip 解压到固定目录，并校验课程项目需要的 9 个 CSV
是否齐全。脚本不会修改 CSV 内容，后续清洗统一交给 PySpark 脚本完成。
"""

from __future__ import annotations

import argparse
from pathlib import Path
from zipfile import ZipFile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ZIP = PROJECT_ROOT / "Brazilian E-Commerce Public Dataset by Olist.zip"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "raw" / "olist"

REQUIRED_FILES = {
    "olist_customers_dataset.csv",
    "olist_geolocation_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_products_dataset.csv",
    "olist_sellers_dataset.csv",
    "product_category_name_translation.csv",
}


def parse_args() -> argparse.Namespace:
    """解析命令行参数，允许在不同机器上指定 zip 和输出目录。"""
    parser = argparse.ArgumentParser(description="解压并校验 Olist 电商公开数据集")
    parser.add_argument("--zip", type=Path, default=DEFAULT_ZIP, help="Olist 数据集 zip 路径")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="CSV 解压目录")
    parser.add_argument("--overwrite", action="store_true", help="允许覆盖同名 CSV 文件")
    return parser.parse_args()


def validate_zip_members(zip_path: Path) -> None:
    """校验 zip 内是否包含所有必需 CSV，避免后续建表时才发现缺文件。"""
    if not zip_path.exists():
        raise FileNotFoundError(f"未找到数据压缩包：{zip_path}")

    with ZipFile(zip_path) as archive:
        actual_files = {Path(name).name for name in archive.namelist() if name.endswith(".csv")}

    missing_files = REQUIRED_FILES - actual_files
    if missing_files:
        missing_text = ", ".join(sorted(missing_files))
        raise RuntimeError(f"数据压缩包缺少必要 CSV：{missing_text}")


def extract_csv_files(zip_path: Path, output_dir: Path, overwrite: bool) -> None:
    """只解压 CSV 文件，并把文件放到统一目录，便于 Spark 和 Hive 使用。"""
    output_dir.mkdir(parents=True, exist_ok=True)

    with ZipFile(zip_path) as archive:
        for member in archive.namelist():
            if not member.endswith(".csv"):
                continue

            filename = Path(member).name
            target = output_dir / filename
            if target.exists() and not overwrite:
                print(f"跳过已存在文件：{target}")
                continue

            with archive.open(member) as source, target.open("wb") as destination:
                destination.write(source.read())
            print(f"已解压：{target}")


def validate_output(output_dir: Path) -> None:
    """校验解压结果，输出缺失文件时给出清晰错误信息。"""
    actual_files = {path.name for path in output_dir.glob("*.csv")}
    missing_files = REQUIRED_FILES - actual_files
    if missing_files:
        missing_text = ", ".join(sorted(missing_files))
        raise RuntimeError(f"解压目录仍缺少必要 CSV：{missing_text}")

    print("Olist 数据准备完成，9 个 CSV 文件已就绪。")


def main() -> None:
    args = parse_args()
    validate_zip_members(args.zip)
    extract_csv_files(args.zip, args.output_dir, args.overwrite)
    validate_output(args.output_dir)


if __name__ == "__main__":
    main()

