# AGENTS.md

## 项目目标

基于 Hive 的电商商品类目销售占比分析与可视化项目。项目目标是围绕商品类目维度，完成数据采集、数据清洗、分层存储、离线统计分析和可视化展示，支撑课程要求中的 Hive + Spark 混合架构。

## 技术栈

- 数据源：Olist 公开电商 CSV 数据集
- 数据采集与落地：本地 CSV 文件、HDFS 或 Hive 外部表
- 数据清洗与规整：Spark / PySpark，用于多表关联、空值处理、字段规整、类目翻译和销售明细宽表生成
- 数据仓库与分析：Hive、Hive SQL，用于 ODS、DWD、DWS、ADS 分层建模和类目销售占比聚合统计
- 可视化：优先使用 Python + Streamlit + ECharts / Plotly 快速实现，也可改为 Vue + ECharts 前端页面
- 调度与运行：课程阶段可使用 Shell 脚本串联数据准备、Spark 清洗、Hive SQL 和可视化启动流程
- 数据格式：CSV 作为原始输入，Parquet / ORC 作为 Hive 分层存储推荐格式

## 当前架构

当前项目已完成首版工程骨架，并已验证本地 Docker Hive/Spark + Streamlit 链路：

- 原始层：保存公开电商 CSV 原始数据。
- Docker 数据层：项目目录挂载到 Hive 容器 `/workspace`，Hive 外部表读取 `data/raw/olist/ods_*` 目录。
- 清洗层：使用 PySpark 完成订单、商品、类目等表的关联、空值处理和字段规整。
- 明细层：生成类目销售明细宽表，包含类目、订单、商品、销量、销售额等字段。
- 汇总层：使用 Hive SQL 统计销售量占比、销售额占比、类目排名、核心类目和弱势类目。
- 可视化层：使用 Streamlit + Plotly 展示饼图、柱状图、类目排名和结构分析结果。

## 推荐数据集

优先推荐使用 Kaggle 的 Brazilian E-Commerce Public Dataset by Olist。该数据集包含约 10 万条巴西电商订单，覆盖订单、商品、类目、价格、客户、支付、评价等多个维度，适合做 Hive 分层建模和 Spark 多表清洗。

备选数据集包括 Kaggle 的 eCommerce behavior data from multi category store，以及 UCI Online Retail。前者数据量很大，适合展示大数据处理能力，但需要从行为事件中筛选 purchase 并补充销量口径；后者字段简单，适合快速实现，但缺少天然类目字段，需要额外映射或人工规整。

## 开发规范

- 修改代码前先读取相关文件，保持最小修改。
- 新增说明性注释默认使用较详细的中文注释。
- 数据处理脚本应优先围绕课程架构拆分为采集、清洗、分层存储、计算分析、可视化五个阶段。
- 不直接删除文件；如需清理文件，先给出建议或移动到临时目录。
- Python 相关执行默认使用项目本地 `.venv`，不使用系统 Python。

## Current Status

已完成 Docker 全链路验证。当前使用 Apache 官方 `apache/hive:4.0.1` 与 `apache/spark:3.5.3` 镜像，Docker Compose 可启动 HiveServer2、Spark Master、Spark Worker。Hive SQL 已成功创建 ODS、DWD、DWS、ADS 分层表，其中 DWD 明细表 112,650 行，DWS 汇总表 74 行，ADS 展示表 74 行。已从 Hive 导出 `data/exports/ads_category_sales_ratio.csv`。Windows 默认端口 8501 可能触发 `WinError 10013`，当前推荐用 `http://127.0.0.1:18501` 访问 Streamlit。

## Recent Changes

- 创建项目级 `AGENTS.md`，记录项目目标、初始架构、开发规范和数据集选型结论。
- 明确主数据集和备选数据集，便于后续进入数据下载、表结构设计和分析指标设计阶段。
- 明确项目推荐技术栈：Spark 负责清洗整合，Hive 负责分层存储和聚合统计，Streamlit / ECharts 负责结果可视化。
- 新增 `.gitignore`，忽略 `.venv`、Python 缓存、本地数据目录、导出结果、日志和 Docker/Hive/Spark 本地运行态。
- 新增 `docker/docker-compose.yml`，用于本地启动 HDFS、Hive Metastore、HiveServer2、Spark Master 和 Spark Worker。
- 新增 `scripts/prepare_data.py`、`scripts/upload_to_hdfs.py`、`scripts/spark_clean_category_sales.py`、`scripts/run_hive_sql.py`、`scripts/export_ads_result.py`、`scripts/build_local_ads.py`。
- 新增 Hive 分层 SQL：ODS 原始表、DWD 类目销售明细表、DWS 类目汇总表、ADS 类目销售占比表。
- 新增 Streamlit 可视化应用和 README 运行说明。
- 准备初始化 Git 仓库并提交首版项目代码、配置、SQL、说明文档和 Olist 数据压缩包。
- 将 Docker Compose 从被镜像代理阻断的 `bde2020/*`、`bitnami/spark` 镜像切换为 Apache 官方 Hive/Spark 镜像。
- 新增 `scripts/prepare_hive_external_dirs.py`，为 Hive 外部表准备稳定目录。
- 修正 ADS 导出脚本，去除 Hive CSV 表名前缀，并使用 `category_type_code` 避免 beeline 中文编码污染。
- 更新 Streamlit 启动说明，默认使用 `127.0.0.1:18501`，规避 Windows 上 8501 端口权限或占用问题。

## Next TODO

- 按 README 运行流程复现系统，生成课程演示截图。
- 如需正式 Spark 写出，优先在 Docker Spark 环境中运行 PySpark，避免 Windows 本机 `winutils.exe` 问题。
- 根据课程报告需要补充架构图、流程图和指标解释。
- 将本次 Docker 验证修正提交并推送到远程公共仓库。
- 使用 `18501` 端口启动 Streamlit 并生成课程演示截图。

## Open Issues

- 原始计划中的 bde2020 Hadoop/Hive 镜像和 bitnami Spark 镜像在当前 Docker 镜像代理下返回 403，已切换为 Apache 官方镜像。
- 当前验证链路未单独启动 HDFS NameNode/DataNode，而是用 Docker 挂载目录作为 Hive 外部表数据源；如课程强制要求展示 HDFS，可后续补充官方 Hadoop 容器启动脚本。
- Windows 本机直接运行 PySpark 写出文件会遇到 `HADOOP_HOME` / `winutils.exe` 缺失问题；当前已提供 Pandas 本地 ADS 演示脚本，正式大数据链路建议放到 Docker Spark 环境运行。
- Windows 上 Streamlit 默认端口 8501 可能触发 `WinError 10013`；推荐显式指定 `--server.port 18501 --server.address 127.0.0.1`。
- Olist 类目名称当前使用英文翻译表，若报告或页面需要中文类目名，需要额外补充中英文映射。

## Architecture Decisions

- 采用 Olist 真实公开电商多表数据作为主数据源，而不是只使用单表模拟销售 CSV。
- 优先通过 Spark 完成多表关联和清洗，再将规整后的类目销售宽表写入 Hive。
- Hive 侧重点放在分层存储、聚合统计和占比分析，贴合“基于 Hive 的电商商品类目销售占比分析与可视化”主题。
- 本机 Python 不直接依赖 PyHive/SASL，Hive SQL 执行和 ADS 导出默认通过 Docker 容器内 beeline 完成，以降低 Windows 环境编译风险。
- 保留 Pandas 本地 ADS 生成脚本作为可视化快速验证入口，但课程主线仍以 PySpark + Hive 为准。
- Docker 默认采用 Apache 官方 Hive/Spark 镜像，优先保证本地可拉取、可运行、可复现。
