"""
Interactive e-commerce sales dashboard.
Data is read from the SQLite database at db/ecommerce_sales.db
(built by db/build_db.py from data/ecommerce_sales.csv).
"""
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# --------------------------------------------------------------------------
# Palette (fixed categorical order + single sequential hue) — see dataviz skill
# --------------------------------------------------------------------------
CATEGORICAL = {
    "blue": "#2a78d6",
    "aqua": "#1baf7a",
    "yellow": "#eda100",
    "green": "#008300",
    "violet": "#4a3aa7",
    "red": "#e34948",
    "magenta": "#e87ba4",
    "orange": "#eb6834",
}
SEQ_BLUE = ["#cde2fb", "#9ec5f4", "#5598e7", "#2a78d6", "#184f95"]
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
SURFACE = "#fcfcfb"

CATEGORY_COLOR = {
    "Beauty": CATEGORICAL["blue"],
    "Clothing": CATEGORICAL["aqua"],
    "Electronics": CATEGORICAL["yellow"],
    "Home": CATEGORICAL["green"],
}

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "db" / "ecommerce_sales.db"

st.set_page_config(
    page_title="E-Commerce Sales Dashboard",
    page_icon="\U0001F4CA",
    layout="wide",
)


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    if not DB_PATH.exists():
        st.error(
            f"Database not found at {DB_PATH}. Run `python db/build_db.py` first."
        )
        st.stop()
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query("SELECT * FROM orders", conn)
    finally:
        conn.close()
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["month"] = df["order_date"].dt.to_period("M").dt.to_timestamp()
    df["net_unit_price"] = df["unit_price"] * (1 - df["discount"])
    return df


def base_layout(fig: go.Figure, title: str) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(color=INK_PRIMARY, size=16)),
        plot_bgcolor=SURFACE,
        paper_bgcolor=SURFACE,
        font=dict(color=INK_SECONDARY, family="system-ui, -apple-system, Segoe UI, sans-serif"),
        margin=dict(l=10, r=10, t=50, b=10),
        hoverlabel=dict(bgcolor="white", font_size=13),
    )
    fig.update_xaxes(showgrid=False, linecolor=GRIDLINE, tickfont=dict(color=INK_MUTED))
    fig.update_yaxes(showgrid=True, gridcolor=GRIDLINE, tickfont=dict(color=INK_MUTED))
    return fig


df_all = load_data()

# --------------------------------------------------------------------------
# Sidebar filters
# --------------------------------------------------------------------------
st.sidebar.header("Filters")

min_date, max_date = df_all["order_date"].min().date(), df_all["order_date"].max().date()
date_range = st.sidebar.date_input(
    "Order date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

categories = sorted(df_all["product_category"].unique())
regions = sorted(df_all["region"].unique())
payment_methods = sorted(df_all["payment_method"].unique())

sel_categories = st.sidebar.multiselect("Product category", categories, default=categories)
sel_regions = st.sidebar.multiselect("Region", regions, default=regions)
sel_payments = st.sidebar.multiselect("Payment method", payment_methods, default=payment_methods)

mask = (
    (df_all["order_date"].dt.date >= start_date)
    & (df_all["order_date"].dt.date <= end_date)
    & (df_all["product_category"].isin(sel_categories))
    & (df_all["region"].isin(sel_regions))
    & (df_all["payment_method"].isin(sel_payments))
)
df = df_all.loc[mask]

st.sidebar.caption(f"{len(df):,} of {len(df_all):,} orders match the current filters.")

st.title("E-Commerce Sales Dashboard")
st.caption("Source: ecommerce_sales_analytics_5000.csv → SQLite (db/ecommerce_sales.db)")

if df.empty:
    st.warning("No orders match the selected filters.")
    st.stop()

# --------------------------------------------------------------------------
# KPI row
# --------------------------------------------------------------------------
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Revenue", f"${df['revenue'].sum():,.0f}")
k2.metric("Orders", f"{len(df):,}")
k3.metric("Avg Order Value", f"${df['revenue'].mean():,.2f}")
k4.metric("Avg Customer Rating", f"{df['customer_rating'].mean():.2f} / 5")
k5.metric("Avg Delivery Days", f"{df['delivery_days'].mean():.1f}")

st.divider()

# --------------------------------------------------------------------------
# Row 1: Revenue trend + Revenue by category
# --------------------------------------------------------------------------
c1, c2 = st.columns((2, 1))

with c1:
    monthly = df.groupby("month", as_index=False)["revenue"].sum().sort_values("month")
    fig = go.Figure(
        go.Scatter(
            x=monthly["month"],
            y=monthly["revenue"],
            mode="lines+markers",
            line=dict(color=CATEGORICAL["blue"], width=2),
            marker=dict(size=6, color=CATEGORICAL["blue"]),
            hovertemplate="%{x|%b %Y}<br>Revenue: $%{y:,.0f}<extra></extra>",
        )
    )
    fig = base_layout(fig, "Monthly Revenue Trend")
    st.plotly_chart(fig, use_container_width=True)

with c2:
    by_cat = df.groupby("product_category", as_index=False)["revenue"].sum().sort_values("revenue")
    fig = go.Figure(
        go.Bar(
            x=by_cat["revenue"],
            y=by_cat["product_category"],
            orientation="h",
            marker_color=[CATEGORY_COLOR[c] for c in by_cat["product_category"]],
            hovertemplate="%{y}<br>Revenue: $%{x:,.0f}<extra></extra>",
        )
    )
    fig = base_layout(fig, "Revenue by Category")
    st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------------------------------
# Row 2: Revenue by region + Payment method share
# --------------------------------------------------------------------------
c3, c4 = st.columns(2)

with c3:
    by_region = df.groupby("region", as_index=False)["revenue"].sum().sort_values("revenue", ascending=False)
    fig = go.Figure(
        go.Bar(
            x=by_region["region"],
            y=by_region["revenue"],
            marker_color=CATEGORICAL["blue"],
            hovertemplate="%{x}<br>Revenue: $%{y:,.0f}<extra></extra>",
        )
    )
    fig = base_layout(fig, "Revenue by Region")
    st.plotly_chart(fig, use_container_width=True)

with c4:
    by_pay = df.groupby("payment_method", as_index=False)["revenue"].sum().sort_values("revenue", ascending=False)
    fig = go.Figure(
        go.Bar(
            x=by_pay["payment_method"],
            y=by_pay["revenue"],
            marker_color=CATEGORICAL["aqua"],
            hovertemplate="%{x}<br>Revenue: $%{y:,.0f}<extra></extra>",
        )
    )
    fig = base_layout(fig, "Revenue by Payment Method")
    st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------------------------------
# Row 3: Category x Region heatmap + Rating distribution by category
# --------------------------------------------------------------------------
c5, c6 = st.columns(2)

with c5:
    pivot = df.pivot_table(
        index="product_category", columns="region", values="revenue", aggfunc="sum", fill_value=0
    )
    fig = go.Figure(
        go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale=SEQ_BLUE,
            hovertemplate="%{y} / %{x}<br>Revenue: $%{z:,.0f}<extra></extra>",
            colorbar=dict(title="Revenue"),
        )
    )
    fig = base_layout(fig, "Revenue: Category x Region")
    st.plotly_chart(fig, use_container_width=True)

with c6:
    fig = go.Figure()
    for cat in categories:
        sub = df.loc[df["product_category"] == cat, "customer_rating"]
        fig.add_trace(
            go.Box(
                y=sub,
                name=cat,
                marker_color=CATEGORY_COLOR[cat],
                boxmean=True,
            )
        )
    fig.update_layout(showlegend=False)
    fig = base_layout(fig, "Customer Rating Distribution by Category")
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# --------------------------------------------------------------------------
# Data table + download
# --------------------------------------------------------------------------
st.subheader("Filtered Orders")
show_cols = [
    "order_id", "order_date", "customer_id", "product_category", "region",
    "quantity", "unit_price", "discount", "payment_method", "delivery_days",
    "customer_rating", "revenue",
]
st.dataframe(df[show_cols].sort_values("order_date"), use_container_width=True, height=350)

st.download_button(
    "Download filtered data as CSV",
    data=df[show_cols].to_csv(index=False).encode("utf-8"),
    file_name="filtered_ecommerce_sales.csv",
    mime="text/csv",
)
