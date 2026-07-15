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
    div[data-testid="stVerticalBlockBorderWrapper"] > div {{
        background-color: {CARD};
        border-radius: 14px;
    }}
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        border-radius: 14px;
    }}
    .panel-title {{
        color: {INK_PRIMARY};
        font-size: 1rem;
        font-weight: 700;
        margin-bottom: 12px;
    }}
    .stat-label {{
        color: {INK_MUTED};
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: .04em;
        text-transform: uppercase;
    }}
    .stat-value {{
        color: {INK_PRIMARY};
        font-size: 1.55rem;
        font-weight: 800;
        margin-top: 3px;
        line-height: 1.2;
    }}
    .stat-sub {{
        color: {INK_MUTED};
        font-size: 0.76rem;
        margin-top: 2px;
    }}
    .delta-up {{ color: {CATEGORICAL["green"]}; font-size: 0.78rem; font-weight: 700; }}
    .delta-down {{ color: {CATEGORICAL["red"]}; font-size: 0.78rem; font-weight: 700; }}
    .delta-flat {{ color: {INK_MUTED}; font-size: 0.78rem; }}
    .mini-progress-track {{
        background: {GRIDLINE};
        border-radius: 4px;
        height: 6px;
        margin-top: 10px;
        overflow: hidden;
    }}
    .mini-progress-fill {{ height: 100%; border-radius: 4px; }}
    .highlight-box {{
        border: 1px solid {CATEGORICAL["green"]};
        background: rgba(62, 207, 62, 0.08);
        border-radius: 10px;
        padding: 10px 14px;
        position: relative;
        min-height: 88px;
    }}
    .highlight-check {{
        position: absolute;
        top: 10px;
        right: 10px;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background: {CATEGORICAL["green"]};
        color: #08150c;
        font-size: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 900;
    }}
    .leaderboard-row {{
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 0;
        border-bottom: 1px solid {GRIDLINE};
    }}
    .leaderboard-row:last-child {{ border-bottom: none; }}
    .avatar-circle {{
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.76rem;
        color: #08150c;
        flex-shrink: 0;
    }}
    .leaderboard-name {{ color: {INK_PRIMARY}; font-size: 0.85rem; font-weight: 600; }}
    .leaderboard-value {{ margin-left: auto; color: {INK_PRIMARY}; font-weight: 700; font-size: 0.85rem; }}
    .big-number {{ font-size: 2.05rem; font-weight: 800; color: {INK_PRIMARY}; margin-top: 4px; }}
    .big-number-caption {{ color: {INK_MUTED}; font-size: 0.78rem; margin-top: 2px; }}
    .stage-row {{ margin-bottom: 14px; }}
    .stage-row:last-child {{ margin-bottom: 0; }}
    .stage-top {{
        display: flex;
        justify-content: space-between;
        font-size: 0.82rem;
        margin-bottom: 6px;
    }}
    .stage-label {{ color: {INK_SECONDARY}; font-weight: 600; }}
    .stage-value {{ color: {INK_PRIMARY}; font-weight: 700; }}
    .recent-item {{ padding: 8px 0; border-bottom: 1px solid {GRIDLINE}; }}
    .recent-item:last-child {{ border-bottom: none; }}
    .recent-name {{ color: {INK_PRIMARY}; font-weight: 600; font-size: 0.83rem; }}
    .recent-meta {{ color: {INK_MUTED}; font-size: 0.74rem; margin-top: 2px; }}
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


def card_layout(fig: go.Figure) -> go.Figure:
    """Chart styling for figures embedded inside a card container (no title, tighter margins)."""
    fig.update_layout(
        plot_bgcolor=CARD,
        paper_bgcolor=CARD,
        font=dict(color=INK_SECONDARY, family="system-ui, -apple-system, Segoe UI, sans-serif"),
        margin=dict(l=10, r=10, t=10, b=10),
        hoverlabel=dict(bgcolor=SURFACE, bordercolor=GRIDLINE, font_size=13, font_color=INK_PRIMARY),
    )
    fig.update_xaxes(showgrid=False, linecolor=GRIDLINE, tickfont=dict(color=INK_MUTED))
    fig.update_yaxes(showgrid=True, gridcolor=GRIDLINE, tickfont=dict(color=INK_MUTED))
    return fig


def fmt_money(x: float) -> str:
    if abs(x) >= 1_000_000:
        return f"${x / 1_000_000:,.1f}M"
    if abs(x) >= 1_000:
        return f"${x / 1_000:,.1f}K"
    return f"${x:,.0f}"


def delta_html(current: float, previous: float, higher_is_better: bool = True, unit: str = "pp") -> str:
    if previous is None or pd.isna(previous) or pd.isna(current):
        return '<span class="delta-flat">— vs prior 30 days</span>'
    diff = current - previous
    if abs(diff) < 1e-9:
        return '<span class="delta-flat">flat vs prior 30 days</span>'
    good = diff > 0 if higher_is_better else diff < 0
    arrow = "▲" if diff > 0 else "▼"
    css = "delta-up" if good else "delta-down"
    value = f"{abs(diff):.1f}{unit}" if unit == "pp" else fmt_money(abs(diff))
    return f'<span class="{css}">{arrow} {value} vs prior 30 days</span>'


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
# Derived metrics for the performance overview (current vs. prior 30-day
# window within the filtered data — the source has one order per calendar
# day, so 30 days gives a stable sample; deltas stay meaningful for any
# date range picked).
# --------------------------------------------------------------------------
STAT_WINDOW_DAYS = 30
last_date = df["order_date"].max().normalize()
cur_start = last_date - pd.Timedelta(days=STAT_WINDOW_DAYS - 1)
prev_start = last_date - pd.Timedelta(days=2 * STAT_WINDOW_DAYS - 1)
prev_end = last_date - pd.Timedelta(days=STAT_WINDOW_DAYS)
cur_win = df[df["order_date"] >= cur_start]
prev_win = df[(df["order_date"] >= prev_start) & (df["order_date"] <= prev_end)]


def _rate(sub: pd.DataFrame, cond) -> float:
    return 100 * cond(sub).mean() if len(sub) else float("nan")


high_rate_cur = _rate(cur_win, lambda d: d["customer_rating"] >= 4)
high_rate_prev = _rate(prev_win, lambda d: d["customer_rating"] >= 4)
low_rate_cur = _rate(cur_win, lambda d: d["customer_rating"] <= 2)
low_rate_prev = _rate(prev_win, lambda d: d["customer_rating"] <= 2)
aov_cur = cur_win["revenue"].mean() if len(cur_win) else float("nan")
aov_prev = prev_win["revenue"].mean() if len(prev_win) else float("nan")

total_revenue = df["revenue"].sum()
largest_order = df.loc[df["revenue"].idxmax()]
avg_delivery = df["delivery_days"].mean()
max_delivery_scale = max(df_all["delivery_days"].max(), 1)
revenue_share = 100 * total_revenue / df_all["revenue"].sum()

# --------------------------------------------------------------------------
# Performance overview — full-width card (KPI stats + gauge + highlight box)
# --------------------------------------------------------------------------
with st.container(border=True):
    st.markdown(
        f'<div class="panel-title">\U0001F4CA Performance overview '
        f"&mdash; {start_date:%b %d} to {end_date:%b %d}</div>",
        unsafe_allow_html=True,
    )
    p1, p2, p3, p4, p5, p6 = st.columns([1.15, 1.15, 1, 1, 1, 1.15])

    with p1:
        st.markdown(
            f"""
            <div class="stat-label">Total revenue</div>
            <div class="stat-value">{fmt_money(total_revenue)}</div>
            <div class="stat-sub">{revenue_share:.0f}% of all-time revenue</div>
            <div class="mini-progress-track">
                <div class="mini-progress-fill" style="width:{min(revenue_share, 100):.0f}%;
                    background:{CATEGORICAL['blue']};"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with p2:
        st.markdown('<div class="stat-label" style="text-align:center;">Avg. delivery time</div>', unsafe_allow_html=True)
        gauge = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=avg_delivery,
                number=dict(suffix=" d", valueformat=".1f", font=dict(size=22, color=INK_PRIMARY)),
                gauge=dict(
                    axis=dict(
                        range=[0, max_delivery_scale], dtick=max_delivery_scale,
                        tickcolor=INK_MUTED, tickfont=dict(size=9),
                    ),
                    bar=dict(color=CATEGORICAL["blue"], thickness=0.35),
                    bgcolor=CARD,
                    borderwidth=0,
                    steps=[
                        dict(range=[0, max_delivery_scale * 0.7], color=SEQ_BLUE[0]),
                        dict(range=[max_delivery_scale * 0.7, max_delivery_scale], color="#3a1c1c"),
                    ],
                ),
            )
        )
        gauge.update_layout(
            height=110,
            margin=dict(l=10, r=10, t=10, b=0),
            paper_bgcolor=CARD,
            font=dict(color=INK_MUTED),
        )
        st.plotly_chart(gauge, use_container_width=True, config={"displayModeBar": False})

    with p3:
        st.markdown(
            f"""
            <div class="stat-label">High-rating rate (30d)</div>
            <div class="stat-value">{high_rate_cur:.1f}%</div>
            <div class="stat-sub">{delta_html(high_rate_cur, high_rate_prev, higher_is_better=True)}</div>
            """,
            unsafe_allow_html=True,
        )

    with p4:
        st.markdown(
            f"""
            <div class="stat-label">Low-rating rate (30d)</div>
            <div class="stat-value">{low_rate_cur:.1f}%</div>
            <div class="stat-sub">{delta_html(low_rate_cur, low_rate_prev, higher_is_better=False)}</div>
            """,
            unsafe_allow_html=True,
        )

    with p5:
        st.markdown(
            f"""
            <div class="stat-label">Avg order value (30d)</div>
            <div class="stat-value">{fmt_money(aov_cur) if not pd.isna(aov_cur) else "—"}</div>
            <div class="stat-sub">{delta_html(aov_cur, aov_prev, higher_is_better=True, unit="$")}</div>
            """,
            unsafe_allow_html=True,
        )

    with p6:
        st.markdown(
            f"""
            <div class="highlight-box">
                <div class="highlight-check">&#10003;</div>
                <div class="stat-label">Largest order</div>
                <div class="stat-value">{fmt_money(largest_order['revenue'])}</div>
                <div class="stat-sub">{largest_order['product_category']} &middot; {largest_order['region']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.write("")

# --------------------------------------------------------------------------
# Second row — 3 columns:
#   left (stacked): orders past week (won/lost-style bars) + new orders trend & recent list
#   middle: top customers leaderboard + forecast + orders-in-range count
#   right: revenue by category (stage-style bars)
# --------------------------------------------------------------------------
left_col, mid_col, right_col = st.columns([2, 1, 1.2])

# The source data has exactly one order per calendar day, so a daily
# won/lost-style split by *count* would show at most one bar a day. Use
# a 14-day window and stack each day's revenue by rating tier instead —
# every day still renders a full, colored bar.
CHART_WINDOW_DAYS = 14
chart_start = last_date - pd.Timedelta(days=CHART_WINDOW_DAYS - 1)
chart_win = df[df["order_date"] >= chart_start]
chart_days = pd.date_range(chart_start, last_date, freq="D")
day_labels = [d.strftime("%d %b") for d in chart_days]

with left_col:
    with st.container(border=True):
        st.markdown(f'<div class="panel-title">\U0001F4C8 Orders — last {CHART_WINDOW_DAYS} days</div>', unsafe_allow_html=True)
        by_day_date = chart_win["order_date"].dt.normalize()
        high_rev = chart_win[chart_win["customer_rating"] >= 4].groupby(by_day_date)["revenue"].sum().reindex(
            chart_days, fill_value=0
        )
        mid_rev = chart_win[chart_win["customer_rating"] == 3].groupby(by_day_date)["revenue"].sum().reindex(
            chart_days, fill_value=0
        )
        low_rev = chart_win[chart_win["customer_rating"] <= 2].groupby(by_day_date)["revenue"].sum().reindex(
            chart_days, fill_value=0
        )
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=day_labels, y=high_rev.values, name="High rating (4-5)",
                marker_color=CATEGORICAL["blue"],
                hovertemplate="%{x}<br>High rating: $%{y:,.0f}<extra></extra>",
            )
        )
        fig.add_trace(
            go.Bar(
                x=day_labels, y=mid_rev.values, name="Mid rating (3)",
                marker_color=CATEGORICAL["violet"],
                hovertemplate="%{x}<br>Mid rating: $%{y:,.0f}<extra></extra>",
            )
        )
        fig.add_trace(
            go.Bar(
                x=day_labels, y=low_rev.values, name="Low rating (1-2)",
                marker_color=CATEGORICAL["yellow"],
                hovertemplate="%{x}<br>Low rating: $%{y:,.0f}<extra></extra>",
            )
        )
        fig.update_layout(
            barmode="stack", height=230,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=11)),
        )
        fig = card_layout(fig)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with st.container(border=True):
        st.markdown('<div class="panel-title">\U0001F195 Orders created</div>', unsafe_allow_html=True)
        trend_col, recent_col = st.columns([1.4, 1])
        with trend_col:
            rev_by_day = chart_win.groupby(by_day_date)["revenue"].sum().reindex(chart_days, fill_value=0)
            fig = go.Figure(
                go.Scatter(
                    x=day_labels, y=rev_by_day.values, mode="lines", fill="tozeroy",
                    line=dict(color=CATEGORICAL["blue"], width=2),
                    fillcolor="rgba(57, 135, 229, 0.15)",
                    hovertemplate="%{x}<br>Revenue: $%{y:,.0f}<extra></extra>",
                )
            )
            fig.update_layout(height=190)
            fig = card_layout(fig)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown(
                f'<div class="stat-sub">Value created past {CHART_WINDOW_DAYS} days: '
                f'<b style="color:{INK_PRIMARY};">{fmt_money(rev_by_day.sum())}</b></div>',
                unsafe_allow_html=True,
            )
        with recent_col:
            st.markdown('<div class="stat-label">Recently created</div>', unsafe_allow_html=True)
            recent = df.sort_values("order_date", ascending=False).head(4)
            items = []
            for _, r in recent.iterrows():
                days_ago = (last_date - r["order_date"]).days
                when = "today" if days_ago == 0 else f"{days_ago}d ago"
                items.append(
                    f"""
                    <div class="recent-item">
                        <div class="recent-name">Customer #{int(r['customer_id'])}</div>
                        <div class="recent-meta">{r['product_category']} &middot; {when} &middot; #{int(r['order_id'])}</div>
                    </div>
                    """
                )
            st.markdown("".join(items), unsafe_allow_html=True)

with mid_col:
    with st.container(border=True):
        st.markdown('<div class="panel-title">\U0001F3C6 Top customers</div>', unsafe_allow_html=True)
        top_customers = df.groupby("customer_id")["revenue"].sum().sort_values(ascending=False).head(3)
        rank_colors = [CATEGORICAL["yellow"], CATEGORICAL["blue"], CATEGORICAL["violet"]]
        rows = []
        for i, (cust_id, rev) in enumerate(top_customers.items()):
            rows.append(
                f"""
                <div class="leaderboard-row">
                    <div class="avatar-circle" style="background:{rank_colors[i]};">{i + 1}</div>
                    <div class="leaderboard-name">Customer #{int(cust_id)}</div>
                    <div class="leaderboard-value">{fmt_money(rev)}</div>
                </div>
                """
            )
        st.markdown("".join(rows), unsafe_allow_html=True)

        span_days = max((df["order_date"].max() - df["order_date"].min()).days + 1, 1)
        forecast_30d = df["revenue"].sum() / span_days * 30
        st.markdown(
            f"""
            <div style="margin-top:18px;">
                <div class="stat-label">Projected 30-day revenue</div>
                <div class="big-number">{fmt_money(forecast_30d)}</div>
                <div class="big-number-caption">Based on current daily average</div>
            </div>
            <div style="margin-top:18px;">
                <div class="big-number">{len(df):,}</div>
                <div class="big-number-caption">Orders in current filter</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

with right_col:
    with st.container(border=True):
        st.markdown('<div class="panel-title">\U0001F4E6 Revenue by category</div>', unsafe_allow_html=True)
        by_cat_stage = df.groupby("product_category")["revenue"].sum().sort_values(ascending=False)
        max_cat_val = by_cat_stage.max()
        rows = []
        for cat, val in by_cat_stage.items():
            width = 100 * val / max_cat_val if max_cat_val else 0
            rows.append(
                f"""
                <div class="stage-row">
                    <div class="stage-top">
                        <span class="stage-label">{cat}</span>
                        <span class="stage-value">{fmt_money(val)}</span>
                    </div>
                    <div class="mini-progress-track" style="margin-top:0;">
                        <div class="mini-progress-fill" style="width:{width:.0f}%;
                            background:{CATEGORY_COLOR[cat]};"></div>
                    </div>
                </div>
                """
            )
        st.markdown("".join(rows), unsafe_allow_html=True)

st.write("")
st.divider()
st.subheader("\U0001F50D Detailed Analytics")

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
