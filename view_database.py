"""
Quick viewer to see what's in the database (superstore.db)
"""
import sqlite3
import os
import pandas as pd

_BASE = os.path.dirname(os.path.abspath(__file__))
conn = sqlite3.connect(os.path.join(_BASE, 'superstore.db'))

print("=" * 60)
print("SUPERSTORE DATA PREVIEW")
print("=" * 60)

print("\n1. CUSTOMERS (first 5):")
df = pd.read_sql_query("SELECT * FROM Customers LIMIT 5", conn)
print(df)

print("\n2. PRODUCTS (first 5):")
df = pd.read_sql_query("SELECT * FROM Products LIMIT 5", conn)
print(df)

print("\n3. LOCATIONS (first 5):")
df = pd.read_sql_query("SELECT * FROM Locations LIMIT 5", conn)
print(df)

print("\n4. RECENT ORDER LINES (last 5 by order date):")
df = pd.read_sql_query("""
    SELECT
        o.Order_ID,
        o.Order_Date,
        c.Customer_Name,
        p.Product_Name,
        p.Category,
        oi.Sales
    FROM Order_Items oi
    JOIN Orders o ON oi.Order_ID = o.Order_ID
    JOIN Customers c ON o.Customer_ID = c.Customer_ID
    JOIN Products p ON oi.Product_Key = p.Product_Key
    ORDER BY o.Order_Date DESC
    LIMIT 5
""", conn)
print(df)

print("\n5. REVENUE BY REGION (this month):")
df = pd.read_sql_query("""
    SELECT
        l.Region,
        COUNT(DISTINCT o.Order_ID) AS order_count,
        SUM(oi.Sales) AS total_revenue
    FROM Order_Items oi
    JOIN Orders o ON oi.Order_ID = o.Order_ID
    JOIN Locations l ON o.Location_ID = l.Location_ID
    WHERE o.Order_Date >= date('now', 'start of month')
    GROUP BY l.Region
    ORDER BY total_revenue DESC
""", conn)
print(df)

conn.close()
