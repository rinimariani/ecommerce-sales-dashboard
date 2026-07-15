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
# Palette — dark theme (fixed categorical order + single sequential hue),
# dark-band steps from the dataviz skill's reference palette.
# --------------------------------------------------------------------------
CATEGORICAL = {
    "blue": "#3987e5",
    "aqua": "#199e70",
    "yellow": "#c98500",
    "green": "#3ecf3e",
    "violet": "#9085e9",
    "red": "#e66767",
    "magenta": "#d55181",
    "orange": "#d95926",
}
# Low -> high magnitude, dark (recedes into the surface) -> bright (pops forward).
SEQ_BLUE = ["#132840", "#184f95", "#1c5cab", "#256abf", "#3987e5", "#6da7ec", "#9ec5f4"]
INK_PRIMARY = "#ffffff"
INK_SECONDARY = "#c3c2b7"
INK_MUTED = "#8f8d86"
GRIDLINE = "#2c2c2a"
SURFACE = "#171715"
PAGE = "#0b0b0a"
CARD = "#1a1a19"

CATEGORY_COLOR = {
    "Beauty": CATEGORICAL["blue"],
    "Clothing": CATEGORICAL["aqua"],
    "Electronics": CATEGORICAL["yellow"],
    "Home": CATEGORICAL["green"],
}

KPI_ACCENTS = [
    CATEGORICAL["blue"],
    CATEGORICAL["aqua"],
    CATEGORICAL["violet"],
    CATEGORICAL["orange"],
    CATEGORICAL["magenta"],
]

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "db" / "ecommerce_sales.db"

st.set_page_config(
    page_title="E-Commerce Sales Dashboard",
    page_icon="\U0001F4CA",
    layout="wide",
)

st.markdown(
    f"""
    <style>
    .stApp {{
        background: radial-gradient(circle at 15% 0%, #14213a 0%, {PAGE} 38%, {PAGE} 100%);
    }}
    section[data-testid="stSidebar"] {{
        background-color: {CARD};
        border-right: 1px solid {GRIDLINE};
    }}
    section[data-testid="stSidebar"] * {{
        color: {INK_SECONDARY};
    }}
    h1, h2, h3, h4, label, p, span {{
        color: {INK_PRIMARY};
    }}
    div[data-testid="stMetric"], div[data-testid="stDataFrame"] {{
        background-color: {CARD};
        border: 1px solid {GRIDLINE};
        border-radius: 12px;
    }}
    hr {{
        border-color: {GRIDLINE} !important;
    }}
    .hero-title {{
        font-size: 2.1rem;
        font-weight: 800;
        background: linear-gradient(90deg, {CATEGORICAL["blue"]}, {CATEGORICAL["aqua"]} 60%, {CATEGORICAL["violet"]});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }}
    .hero-caption {{
        color: {INK_MUTED};
        font-size: 0.92rem;
        margin-top: 2px;
    }}
    .kpi-card {{
        background: {CARD};
        border: 1px solid {GRIDLINE};
        border-radius: 12px;
        padding: 14px 18px;
        min-height: 96px;
    }}
    .kpi-label {{
        color: {INK_MUTED};
        font-size: 0.76rem;
        font-weight: 700;
        letter-spacing: .04em;
        text-transform: uppercase;
    }}
    .kpi-value {{
        color: {INK_PRIMARY};
        font-size: 1.65rem;
        font-weight: 700;
        margin-top: 4px;
    }}
    </style>
    """,
    unsafe_allow_html=True,
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
        hoverlabel=dict(bgcolor=CARD, bordercolor=GRIDLINE, font_size=13, font_color=INK_PRIMARY),
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

st.markdown('<div class="hero-title">\U0001F6CD️ E-Commerce Sales Dashboard</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-caption">Source: ecommerce_sales_analytics_5000.csv &rarr; SQLite '
    "(db/ecommerce_sales.db)</div>",
    unsafe_allow_html=True,
)
st.write("")

if df.empty:
    st.warning("No orders match the selected filters.")
    st.stop()

# --------------------------------------------------------------------------
# KPI row
# --------------------------------------------------------------------------
kpis = [
    ("\U0001F4B0 Total Revenue", f"${df['revenue'].sum():,.0f}"),
    ("\U0001F4E6 Orders", f"{len(df):,}"),
    ("\U0001F9FE Avg Order Value", f"${df['revenue'].mean():,.2f}"),
    ("\U00002B50 Avg Rating", f"{df['customer_rating'].mean():.2f} / 5"),
    ("\U0001F69A Avg Delivery Days", f"{df['delivery_days'].mean():.1f}"),
]
kpi_cols = st.columns(5)
for col, (label, value), accent in zip(kpi_cols, kpis, KPI_ACCENTS):
    with col:
        st.markdown(
            f"""
            <div class="kpi-card" style="border-left:4px solid {accent};">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.write("")
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
    fig = base_layout(fig, "📈 Monthly Revenue Trend")
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
    fig = base_layout(fig, "🏷️ Revenue by Category")
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
    fig = base_layout(fig, "🌍 Revenue by Region")
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
    fig = base_layout(fig, "💳 Revenue by Payment Method")
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
    fig = base_layout(fig, "🔥 Revenue: Category x Region")
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
    fig = base_layout(fig, "⭐ Rating Distribution by Category")
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# --------------------------------------------------------------------------
# Data table + download
# --------------------------------------------------------------------------
st.subheader("🗂️ Filtered Orders")
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
