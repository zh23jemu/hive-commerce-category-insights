# 基于 Hive 的电商商品类目销售占比分析与可视化

## 项目概述

本项目使用 Brazilian E-Commerce Public Dataset by Olist 作为数据源，围绕电商商品类目维度完成数据清洗、Hive 分层建模、销售占比统计和可视化展示。项目技术栈为 Python、PySpark、Docker、HDFS、Hive 和 Streamlit，适合大数据专业企业实习课或课程设计展示。

## 技术栈

- Python：项目脚本和可视化主语言。
- PySpark：清洗订单、商品、类目等多表数据，生成类目销售明细宽表。
- Docker：本地搭建 HDFS、Hive、Spark 环境。
- HDFS：存放原始数据和分层数据。
- Hive：建立 ODS、DWD、DWS、ADS 分层表并执行聚合统计。
- Streamlit + Plotly：展示类目销售额占比、销量排行和明细表。

## 项目结构

```text
.
├── app/                         # Streamlit 可视化应用
├── data/                        # 原始数据、清洗结果和导出结果，默认不入库
├── docker/                      # Docker Compose 本地大数据环境
├── scripts/                     # 数据准备、Spark 清洗、Hive 执行、结果导出脚本
├── sql/                         # Hive 分层建表和统计 SQL
├── AGENTS.md                    # 项目维护状态和开发约束
├── README.md                    # 项目说明
└── requirements.txt             # Python 依赖
```

## 环境要求

- Windows 机器建议安装 Docker Desktop。
- Python 使用项目本地 `.venv`，不要直接使用系统 Python。
- 数据压缩包放在项目根目录：`Brazilian E-Commerce Public Dataset by Olist.zip`。

## 启动方法

1. 创建并安装 Python 本地环境。

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

2. 解压并校验 Olist 数据。

```powershell
.venv\Scripts\python.exe scripts\prepare_data.py
```

3. 启动本地 Docker 大数据环境。

```powershell
docker compose -f docker\docker-compose.yml up -d
```

4. 上传原始 CSV 到 HDFS。

```powershell
.venv\Scripts\python.exe scripts\upload_to_hdfs.py
```

5. 运行 PySpark 清洗任务。

```powershell
.venv\Scripts\python.exe scripts\spark_clean_category_sales.py
```

如果在 Windows 本机直接运行 PySpark 且没有配置 `HADOOP_HOME`，写出文件可能会提示缺少 `winutils.exe`。正式流程建议在 Docker Spark 环境中运行；如果只是验证可视化页面，可以先用 Pandas 生成同口径 ADS 演示结果：

```powershell
.venv\Scripts\python.exe scripts\build_local_ads.py
```

6. 执行 Hive 分层 SQL。

```powershell
.venv\Scripts\python.exe scripts\run_hive_sql.py
```

7. 导出 ADS 结果并启动可视化。

```powershell
.venv\Scripts\python.exe scripts\export_ads_result.py
.venv\Scripts\python.exe -m streamlit run app\streamlit_app.py
```

## 关键统计口径

- 销量：Olist 订单明细表每一行计为 1 件商品。
- 销售额：默认使用 `price` 字段，不把运费计入主销售额。
- 含运费销售额：保留 `price + freight_value` 作为扩展指标。
- 商品数量：默认统计类目下不同 `product_id` 的数量。
- 类目名称：优先使用 `product_category_name_translation.csv` 中的英文类目名。

## 注意事项

- `data/raw/`、`data/processed/`、`data/exports/` 默认已加入 `.gitignore`。
- Docker 首次启动需要拉取镜像，耗时取决于网络环境。
- `scripts/export_ads_result.py` 默认通过 Docker 容器内的 `beeline` 导出 ADS 结果，避免 Windows 本机安装 Hive SASL 客户端。
- Streamlit 默认读取 `data/exports/ads_category_sales_ratio.csv`，因此需要先导出 ADS 结果。
- Hive ODS 表默认读取 HDFS 的 `/data/olist/raw/` 目录，因此需要先执行 `scripts/upload_to_hdfs.py`。
