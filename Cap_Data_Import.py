import pandas as pd
from urllib.parse import quote_plus
from sqlalchemy import create_engine, text

# -----------------------------
# Connection settings
# -----------------------------
username = "root"
password = quote_plus("password")
host = "localhost"
port = 3306
database = "superstore_db"

# -----------------------------
# Create database if needed
# -----------------------------
server_engine = create_engine(
    f"mysql+pymysql://{username}:{password}@{host}:{port}"
)

with server_engine.connect() as conn:
    conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {database}"))
    conn.commit()

# -----------------------------
# Connect to target database
# -----------------------------
engine = create_engine(
    f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
)

drop_statements = [
    "DROP TABLE IF EXISTS Order_Items",
    "DROP TABLE IF EXISTS Orders",
    "DROP TABLE IF EXISTS Products",
    "DROP TABLE IF EXISTS Locations",
    "DROP TABLE IF EXISTS Customers"
]

with engine.connect() as conn:
    for stmt in drop_statements:
        conn.execute(text(stmt))
    conn.commit()

# -----------------------------
# Create tables
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
        Product_Key INT PRIMARY KEY,
        Product_ID VARCHAR(30),
        Category VARCHAR(50),
        Sub_Category VARCHAR(50),
        Product_Name VARCHAR(255)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS Locations (
        Location_ID INT PRIMARY KEY,
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
        Location_ID INT,
        FOREIGN KEY (Customer_ID) REFERENCES Customers(Customer_ID),
        FOREIGN KEY (Location_ID) REFERENCES Locations(Location_ID)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS Order_Items (
        Order_ID VARCHAR(20),
        Product_Key INT,
        Sales DECIMAL(10,2),
        PRIMARY KEY (Order_ID, Product_Key),
        FOREIGN KEY (Order_ID) REFERENCES Orders(Order_ID),
        FOREIGN KEY (Product_Key) REFERENCES Products(Product_Key)
    )
    """
]

with engine.connect() as conn:
    for stmt in create_table_statements:
        conn.execute(text(stmt))
    conn.commit()

# -----------------------------
# Read CSV files
# -----------------------------
customers_df = pd.read_csv("Customers.csv")
products_df = pd.read_csv("Products.csv")
locations_df = pd.read_csv("Locations.csv")
orders_df = pd.read_csv("Orders.csv")
order_items_df = pd.read_csv("Order_Items.csv")


# -----------------------------
# Load into MySQL in dependency order
# -----------------------------
customers_df.to_sql("Customers", con=engine, if_exists="append", index=False)
locations_df.to_sql("Locations", con=engine, if_exists="append", index=False)
orders_df.to_sql("Orders", con=engine, if_exists="append", index=False)
products_df.to_sql("Products", con=engine, if_exists="append", index=False)
order_items_df.to_sql("Order_Items", con=engine, if_exists="append", index=False)

print("All tables imported successfully.")

