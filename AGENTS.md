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

当前项目已完成首版工程骨架，采用 Python + PySpark + Docker HDFS/Hive + Streamlit 架构：

- 原始层：保存公开电商 CSV 原始数据。
- HDFS 层：通过 Docker NameNode / DataNode 存放 Olist 原始 CSV。
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

已完成项目首版落地实现，并准备初始化 Git 仓库与提交首版。仓库已包含 Docker Compose 本地大数据环境、Olist 数据准备脚本、PySpark 类目销售清洗脚本、Hive ODS/DWD/DWS/ADS 分层 SQL、ADS 导出脚本、Pandas 本地演示结果生成脚本、Streamlit 可视化页面和 README 运行说明。已解压并校验 Olist 9 个 CSV，已用 Pandas 生成本地 ADS 演示结果，Streamlit 页面已在 `http://localhost:8501` 通过 HTTP 冒烟检查。

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

## Next TODO

- 启动 Docker Compose，验证 HDFS、Hive、Spark 容器在本机环境中能正常运行。
- 执行 `scripts/upload_to_hdfs.py`，把 Olist 原始 CSV 上传到 HDFS `/data/olist/raw/`。
- 执行 `scripts/run_hive_sql.py`，验证 Hive ODS/DWD/DWS/ADS 分层 SQL 全链路。
- 如需正式 Spark 写出，优先在 Docker Spark 环境中运行 PySpark，避免 Windows 本机 `winutils.exe` 问题。
- 根据课程报告需要补充架构图、流程图和指标解释。
- 首版提交完成后，如需远端同步，再根据用户明确要求配置远程仓库并推送。

## Open Issues

- Docker 全链路尚未在本轮启动验证，后续需要确认镜像拉取、容器健康状态和 HiveServer2 连接。
- Windows 本机直接运行 PySpark 写出文件会遇到 `HADOOP_HOME` / `winutils.exe` 缺失问题；当前已提供 Pandas 本地 ADS 演示脚本，正式大数据链路建议放到 Docker Spark 环境运行。
- Olist 类目名称当前使用英文翻译表，若报告或页面需要中文类目名，需要额外补充中英文映射。

## Architecture Decisions

- 采用 Olist 真实公开电商多表数据作为主数据源，而不是只使用单表模拟销售 CSV。
- 优先通过 Spark 完成多表关联和清洗，再将规整后的类目销售宽表写入 Hive。
- Hive 侧重点放在分层存储、聚合统计和占比分析，贴合“基于 Hive 的电商商品类目销售占比分析与可视化”主题。
- 本机 Python 不直接依赖 PyHive/SASL，Hive SQL 执行和 ADS 导出默认通过 Docker 容器内 beeline 完成，以降低 Windows 环境编译风险。
- 保留 Pandas 本地 ADS 生成脚本作为可视化快速验证入口，但课程主线仍以 PySpark + Hive 为准。
