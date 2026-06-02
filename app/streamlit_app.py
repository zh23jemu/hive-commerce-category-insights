"""电商商品类目销售占比可视化页面。

页面默认读取 `data/exports/ads_category_sales_ratio.csv`，这样即使演示时 Hive
服务没有持续运行，也可以展示已导出的分析结果。若需要实时查询 Hive，可以先运行
`scripts/export_ads_result.py` 刷新导出文件。
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULT = PROJECT_ROOT / "data" / "exports" / "ads_category_sales_ratio.csv"


st.set_page_config(page_title="电商商品类目销售占比分析", page_icon="📊", layout="wide")


@st.cache_data(show_spinner=False)
def load_result(path: Path) -> pd.DataFrame:
    """读取 ADS 结果 CSV，并统一处理数值列类型。"""
    if not path.exists():
        return pd.DataFrame()

    data = pd.read_csv(path)
    if "category_type_code" in data.columns:
        # Hive 容器内 beeline 在部分 Windows 终端会把中文输出编码打乱，因此导出时使用稳定的英文编码，
        # 页面加载后再映射为中文展示，保证图表和表格始终可读。
        data["category_type"] = data["category_type_code"].map(
            {"core": "核心类目", "support": "辅助类目", "weak": "弱势类目"}
        ).fillna(data["category_type_code"])

    numeric_columns = [
        "sales_quantity",
        "sales_amount",
        "sales_amount_with_freight",
        "order_count",
        "product_count",
        "quantity_ratio",
        "sales_amount_ratio",
        "sales_amount_rank",
    ]
    for column in numeric_columns:
        if column in data.columns:
            data[column] = pd.to_numeric(data[column], errors="coerce")
    return data


def render_empty_state() -> None:
    """结果文件不存在时给出清晰的下一步操作提示。"""
    st.title("电商商品类目销售占比分析")
    st.warning("尚未找到 ADS 结果文件，请先完成 Hive 统计并导出结果。")
    st.code(
        ".venv\\Scripts\\python.exe scripts\\export_ads_result.py",
        language="powershell",
    )


def render_dashboard(data: pd.DataFrame) -> None:
    """渲染类目销售占比仪表盘，包含核心指标、图表和明细表。"""
    data = data.sort_values("sales_amount_rank")
    top_n = st.sidebar.slider("TopN 类目数量", min_value=5, max_value=30, value=10, step=5)
    top_data = data.head(top_n)

    st.title("电商商品类目销售占比分析")
    st.caption("数据源：Brazilian E-Commerce Public Dataset by Olist；统计口径：订单明细每行计为 1 件，销售额使用商品价格 price。")

    metric_cols = st.columns(4)
    metric_cols[0].metric("类目数量", f"{data['category_name_en'].nunique():,}")
    metric_cols[1].metric("总销量", f"{int(data['sales_quantity'].sum()):,}")
    metric_cols[2].metric("总销售额", f"{data['sales_amount'].sum():,.2f}")
    metric_cols[3].metric("商品种类数", f"{int(data['product_count'].sum()):,}")

    left, right = st.columns([1, 1])
    with left:
        fig = px.pie(
            top_data,
            names="category_name_en",
            values="sales_amount",
            title=f"Top{top_n} 类目销售额占比",
            hole=0.35,
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)

    with right:
        fig = px.bar(
            top_data.sort_values("sales_quantity"),
            x="sales_quantity",
            y="category_name_en",
            orientation="h",
            title=f"Top{top_n} 类目销量排行",
            labels={"sales_quantity": "销量", "category_name_en": "商品类目"},
        )
        st.plotly_chart(fig, use_container_width=True)

    fig = px.bar(
        top_data,
        x="category_name_en",
        y="sales_amount",
        color="category_type",
        title=f"Top{top_n} 类目销售额",
        labels={"sales_amount": "销售额", "category_name_en": "商品类目", "category_type": "类目类型"},
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("类目销售结构明细")
    st.dataframe(
        data[
            [
                "sales_amount_rank",
                "category_name_en",
                "category_type",
                "sales_quantity",
                "quantity_ratio",
                "sales_amount",
                "sales_amount_ratio",
                "order_count",
                "product_count",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )


result = load_result(DEFAULT_RESULT)
if result.empty:
    render_empty_state()
else:
    render_dashboard(result)
