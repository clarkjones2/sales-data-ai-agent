import os

import pandas as pd
from sqlalchemy import create_engine, event, text

# -----------------------------
# SQLite database file (created on first connect)
# -----------------------------
# Resolve paths relative to this script so imports work from any cwd
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_DB_PATH = os.path.join(_SCRIPT_DIR, "superstore.db")

# -----------------------------
# Engine with foreign keys enforced (MySQL enforces by default)
# -----------------------------
engine = create_engine(f"sqlite:///{SQLITE_DB_PATH}")


@event.listens_for(engine, "connect")
def _sqlite_enable_foreign_keys(dbapi_connection, _connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


drop_statements = [
    "DROP TABLE IF EXISTS Order_Items",
    "DROP TABLE IF EXISTS Orders",
    "DROP TABLE IF EXISTS Products",
    "DROP TABLE IF EXISTS Locations",
    "DROP TABLE IF EXISTS Customers",
]

with engine.connect() as conn:
    for stmt in drop_statements:
        conn.execute(text(stmt))
    conn.commit()

# -----------------------------
# Create tables (SQLite-compatible DDL)
# -----------------------------
create_table_statements = [
    """
    CREATE TABLE IF NOT EXISTS Customers (
        Customer_ID VARCHAR(20) PRIMARY KEY,
        Customer_Name VARCHAR(100),
        Segment VARCHAR(50)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS Products (
        Product_Key INTEGER PRIMARY KEY,
        Product_ID VARCHAR(30),
        Category VARCHAR(50),
        Sub_Category VARCHAR(50),
        Product_Name VARCHAR(255)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS Locations (
        Location_ID INTEGER PRIMARY KEY,
        Country VARCHAR(50),
        City VARCHAR(100),
        State VARCHAR(100),
        Postal_Code VARCHAR(5),
        Region VARCHAR(50)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS Orders (
        Order_ID VARCHAR(20) PRIMARY KEY,
        Order_Date DATE,
        Ship_Date DATE,
        Ship_Mode VARCHAR(50),
        Customer_ID VARCHAR(20),
        Location_ID INTEGER,
        FOREIGN KEY (Customer_ID) REFERENCES Customers(Customer_ID),
        FOREIGN KEY (Location_ID) REFERENCES Locations(Location_ID)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS Order_Items (
        Order_ID VARCHAR(20),
        Product_Key INTEGER,
        Sales DECIMAL(10,2),
        PRIMARY KEY (Order_ID, Product_Key),
        FOREIGN KEY (Order_ID) REFERENCES Orders(Order_ID),
        FOREIGN KEY (Product_Key) REFERENCES Products(Product_Key)
    )
    """,
]

with engine.connect() as conn:
    for stmt in create_table_statements:
        conn.execute(text(stmt))
    conn.commit()

# -----------------------------
# Read CSV files (same folder as this script)
# -----------------------------
customers_df = pd.read_csv(os.path.join(_SCRIPT_DIR, "Customers.csv"))
products_df = pd.read_csv(os.path.join(_SCRIPT_DIR, "Products.csv"))
locations_df = pd.read_csv(os.path.join(_SCRIPT_DIR, "Locations.csv"))
orders_df = pd.read_csv(os.path.join(_SCRIPT_DIR, "Orders.csv"))
order_items_df = pd.read_csv(os.path.join(_SCRIPT_DIR, "Order_Items.csv"))

# -----------------------------
# Load into SQLite in dependency order
# -----------------------------
customers_df.to_sql("Customers", con=engine, if_exists="append", index=False)
locations_df.to_sql("Locations", con=engine, if_exists="append", index=False)
orders_df.to_sql("Orders", con=engine, if_exists="append", index=False)
products_df.to_sql("Products", con=engine, if_exists="append", index=False)
order_items_df.to_sql("Order_Items", con=engine, if_exists="append", index=False)

print(f"All tables imported successfully into {SQLITE_DB_PATH}")
