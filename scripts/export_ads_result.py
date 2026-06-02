"""导出 ADS 类目销售占比结果。

Windows 本机直接安装 Hive Python 客户端经常会遇到 SASL 编译问题，因此这里
不依赖 PyHive，而是复用 Docker HiveServer2 容器内置的 beeline。脚本负责调用
容器内 beeline 查询 ADS 表，并把结果保存为 Streamlit 可直接读取的 CSV。
"""

from __future__ import annotations

import argparse
import csv
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "exports" / "ads_category_sales_ratio.csv"


def parse_args() -> argparse.Namespace:
    """解析 Hive 连接参数、Docker 容器名称和导出路径。"""
    parser = argparse.ArgumentParser(description="导出 ADS 类目销售占比结果")
    parser.add_argument("--container", default="olist-hive-server", help="HiveServer2 容器名")
    parser.add_argument("--jdbc-url", default="jdbc:hive2://localhost:10000/default", help="容器内 beeline 连接地址")
    parser.add_argument("--database", default="olist_category_insights", help="Hive 数据库")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="导出 CSV 路径")
    return parser.parse_args()


def run_beeline(container: str, jdbc_url: str, database: str) -> str:
    """在 Hive 容器内执行查询，并返回 csv2 格式的标准输出。"""
    query = f"""
    USE {database};
    SELECT
      category_name_en AS category_name_en,
      sales_quantity AS sales_quantity,
      sales_amount AS sales_amount,
      sales_amount_with_freight AS sales_amount_with_freight,
      order_count AS order_count,
      product_count AS product_count,
      quantity_ratio AS quantity_ratio,
      sales_amount_ratio AS sales_amount_ratio,
      sales_amount_rank AS sales_amount_rank,
      CASE
        WHEN sales_amount_rank <= 10 THEN 'core'
        WHEN sales_amount_rank <= 30 THEN 'support'
        ELSE 'weak'
      END AS category_type_code
    FROM ads_category_sales_ratio
    ORDER BY sales_amount_rank;
    """
    command = [
        "docker",
        "exec",
        container,
        "beeline",
        "-u",
        jdbc_url,
        "--showHeader=true",
        "--outputformat=csv2",
        "-e",
        query,
    ]
    result = subprocess.run(command, check=True, text=True, capture_output=True)
    return result.stdout


def parse_beeline_csv(output: str) -> list[list[str]]:
    """过滤 beeline 日志行，只保留真正的 CSV 表头和数据行。"""
    rows: list[list[str]] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("Connecting to", "Connected to", "Driver:", "Transaction isolation:")):
            continue
        if line.startswith(("INFO", "WARN", "No rows selected")):
            continue
        rows.append(next(csv.reader([line])))
    return rows


def write_csv(rows: list[list[str]], output: Path) -> None:
    """把 beeline 查询结果写入本地 CSV，供 Streamlit 离线展示。"""
    if not rows:
        raise RuntimeError("Hive 查询没有返回任何可导出的 ADS 数据。")

    rows[0] = [column.split(".")[-1] for column in rows[0]]
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    beeline_output = run_beeline(args.container, args.jdbc_url, args.database)
    rows = parse_beeline_csv(beeline_output)
    write_csv(rows, args.output)
    print(f"ADS 结果已导出：{args.output}")


if __name__ == "__main__":
    main()
