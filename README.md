# E-Commerce Sales Dashboard

Interactive dashboard for the `ecommerce_sales_analytics_5000.csv` dataset (5,000 orders,
Jan 2022 – Sep 2035), built with **Streamlit** + **Plotly**, backed by a **SQLite** database.

## Live demo

_Add the Streamlit Community Cloud URL here once deployed._

## What it shows

- KPI tiles: total revenue, order count, average order value, average rating, average delivery days
- Filters: order date range, product category, region, payment method
- Monthly revenue trend
- Revenue by category, region, and payment method
- Revenue heatmap by category x region
- Customer rating distribution by category
- Filtered order table with CSV export

## Project structure

```
ecommerce-sales-dashboard/
├── app.py                    # Streamlit dashboard
├── data/
│   └── ecommerce_sales.csv   # source data
├── db/
│   ├── build_db.py           # CSV -> SQLite ETL script
│   └── ecommerce_sales.db    # SQLite database (committed, built from the CSV)
├── requirements.txt
├── .streamlit/config.toml    # theme
└── README.md
```

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# (re)build the database from the CSV — only needed if data/ecommerce_sales.csv changes
python db/build_db.py

streamlit run app.py
```

The app opens at `http://localhost:8501`.

## Deploy publicly (Streamlit Community Cloud — free)

1. Go to https://share.streamlit.io and sign in with GitHub.
2. Click **New app**.
3. Pick this repository, branch `main`, main file path `app.py`.
4. Click **Deploy**. Streamlit Cloud installs `requirements.txt` and runs the app;
   `db/ecommerce_sales.db` is already in the repo, so no extra setup is needed.
5. Once deployed, copy the public URL into the "Live demo" section above.

## Rebuilding the database

The dashboard reads from `db/ecommerce_sales.db`. If you change the CSV, regenerate it with:

```bash
python db/build_db.py
```

This recreates the `orders` table (with indexes on date, category, region, and payment
method) and re-inserts every row from `data/ecommerce_sales.csv`.
