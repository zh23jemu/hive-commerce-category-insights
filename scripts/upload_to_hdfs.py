"""把 Olist 原始 CSV 上传到 HDFS。

Hive 外部表通常指向 HDFS 目录，而不是本地文件。该脚本会为每个 CSV 创建一个
稳定目录，并把文件上传为 `data.csv`，从而让 ODS 表的 LOCATION 可以保持固定。
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_DIR = PROJECT_ROOT / "data" / "raw" / "olist"
DEFAULT_HDFS_BASE = "/data/olist/raw"

CSV_TO_HDFS_DIR = {
    "olist_customers_dataset.csv": "olist_customers_dataset",
    "olist_geolocation_dataset.csv": "olist_geolocation_dataset",
    "olist_order_items_dataset.csv": "olist_order_items_dataset",
    "olist_order_payments_dataset.csv": "olist_order_payments_dataset",
    "olist_order_reviews_dataset.csv": "olist_order_reviews_dataset",
    "olist_orders_dataset.csv": "olist_orders_dataset",
    "olist_products_dataset.csv": "olist_products_dataset",
    "olist_sellers_dataset.csv": "olist_sellers_dataset",
    "product_category_name_translation.csv": "product_category_name_translation",
}


def parse_args() -> argparse.Namespace:
    """解析本地 CSV 目录、目标 HDFS 目录和 Docker 容器名称。"""
    parser = argparse.ArgumentParser(description="上传 Olist CSV 到本地 Docker HDFS")
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR, help="本地 Olist CSV 目录")
    parser.add_argument("--hdfs-base", default=DEFAULT_HDFS_BASE, help="HDFS 原始数据根目录")
    parser.add_argument("--namenode-container", default="olist-namenode", help="NameNode 容器名")
    return parser.parse_args()


def docker_hdfs(container: str, *hdfs_args: str) -> None:
    """通过 NameNode 容器执行 HDFS 命令，避免依赖宿主机安装 Hadoop 客户端。"""
    command = ["docker", "exec", container, "hdfs", "dfs", *hdfs_args]
    subprocess.run(command, check=True)


def upload_file(container: str, local_file: Path, hdfs_dir: str) -> None:
    """创建 HDFS 目录并上传单个 CSV，覆盖旧的同名文件。"""
    if not local_file.exists():
        raise FileNotFoundError(f"本地 CSV 不存在：{local_file}")

    docker_hdfs(container, "-mkdir", "-p", hdfs_dir)
    docker_hdfs(container, "-put", "-f", f"/workspace/{local_file.relative_to(PROJECT_ROOT).as_posix()}", f"{hdfs_dir}/data.csv")
    print(f"已上传：{local_file.name} -> {hdfs_dir}/data.csv")


def main() -> None:
    args = parse_args()
    for csv_name, hdfs_dir_name in CSV_TO_HDFS_DIR.items():
        upload_file(
            container=args.namenode_container,
            local_file=args.raw_dir / csv_name,
            hdfs_dir=f"{args.hdfs_base.rstrip('/')}/{hdfs_dir_name}",
        )
    print("Olist 原始 CSV 已全部上传到 HDFS。")


if __name__ == "__main__":
    main()

