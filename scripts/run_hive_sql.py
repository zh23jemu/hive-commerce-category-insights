"""顺序执行 Hive SQL 文件。

脚本默认通过 Docker HiveServer2 容器内置的 beeline 执行 SQL，避免宿主机额外
安装 Hive 客户端。SQL 文件会通过项目目录挂载到容器的 `/workspace` 下读取。
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SQL_FILES = [
    PROJECT_ROOT / "sql" / "01_create_database.sql",
    PROJECT_ROOT / "sql" / "02_create_ods_tables.sql",
    PROJECT_ROOT / "sql" / "03_create_dwd_tables.sql",
    PROJECT_ROOT / "sql" / "04_create_dws_ads_tables.sql",
]


def parse_args() -> argparse.Namespace:
    """解析 Hive 连接参数和待执行 SQL 文件列表。"""
    parser = argparse.ArgumentParser(description="执行 Hive 分层建表和统计 SQL")
    parser.add_argument("--container", default="olist-hive-server", help="HiveServer2 容器名")
    parser.add_argument("--jdbc-url", default="jdbc:hive2://localhost:10000/default", help="HiveServer2 JDBC 地址")
    parser.add_argument("--user", default="hive", help="Hive 用户名")
    parser.add_argument("--password", default="", help="Hive 密码，本地测试通常为空")
    parser.add_argument("--local-beeline", action="store_true", help="使用宿主机 beeline，而不是 Docker 容器内 beeline")
    parser.add_argument("--sql", nargs="*", type=Path, default=DEFAULT_SQL_FILES, help="按顺序执行的 SQL 文件")
    return parser.parse_args()


def run_sql_file(args: argparse.Namespace, sql_file: Path) -> None:
    """执行单个 SQL 文件，失败时保留 beeline 原始错误输出便于定位。"""
    if not sql_file.exists():
        raise FileNotFoundError(f"SQL 文件不存在：{sql_file}")

    sql_path = str(sql_file)
    command = ["beeline"] if args.local_beeline else ["docker", "exec", args.container, "beeline"]
    if not args.local_beeline:
        sql_path = f"/workspace/{sql_file.relative_to(PROJECT_ROOT).as_posix()}"

    command.extend(["-u", args.jdbc_url, "-n", args.user, "-p", args.password, "-f", sql_path])
    print(f"正在执行 SQL：{sql_file}")
    subprocess.run(command, check=True)


def main() -> None:
    args = parse_args()
    for sql_file in args.sql:
        run_sql_file(args, sql_file)
    print("Hive SQL 执行完成。")


if __name__ == "__main__":
    main()
