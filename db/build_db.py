"""
Builds db/ecommerce_sales.db from data/ecommerce_sales.csv.

Run once (or whenever the CSV changes):
    python db/build_db.py
"""
import csv
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "data" / "ecommerce_sales.csv"
DB_PATH = BASE_DIR / "db" / "ecommerce_sales.db"

SCHEMA = """
DROP TABLE IF EXISTS orders;
CREATE TABLE orders (
    order_id        INTEGER PRIMARY KEY,
    order_date      TEXT NOT NULL,
    customer_id     INTEGER NOT NULL,
    product_category TEXT NOT NULL,
    region          TEXT NOT NULL,
    quantity        INTEGER NOT NULL,
    unit_price      REAL NOT NULL,
    discount        REAL NOT NULL,
    payment_method  TEXT NOT NULL,
    delivery_days   INTEGER NOT NULL,
    customer_rating REAL NOT NULL,
    revenue         REAL NOT NULL
);
CREATE INDEX idx_orders_date ON orders (order_date);
CREATE INDEX idx_orders_category ON orders (product_category);
CREATE INDEX idx_orders_region ON orders (region);
CREATE INDEX idx_orders_payment ON orders (payment_method);
"""


def parse_date(mdy: str) -> str:
    """Convert 'M/D/YYYY' -> 'YYYY-MM-DD' so SQLite can sort/filter it as text."""
    month, day, year = mdy.split("/")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def main() -> None:
    if not CSV_PATH.exists():
        raise SystemExit(f"CSV not found: {CSV_PATH}")

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [
            (
                int(r["order_id"]),
                parse_date(r["order_date"]),
                int(r["customer_id"]),
                r["product_category"],
                r["region"],
                int(r["quantity"]),
                float(r["unit_price"]),
                float(r["discount"]),
                r["payment_method"],
                int(r["delivery_days"]),
                float(r["customer_rating"]),
                float(r["revenue"]),
            )
            for r in reader
        ]

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(SCHEMA)
        conn.executemany(
            """INSERT INTO orders (
                order_id, order_date, customer_id, product_category, region,
                quantity, unit_price, discount, payment_method, delivery_days,
                customer_rating, revenue
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            rows,
        )
        conn.commit()
    finally:
        conn.close()

    print(f"Inserted {len(rows)} rows into {DB_PATH}")


if __name__ == "__main__":
    main()
