"""
Quick viewer to see what's in the database
"""
import sqlite3
import pandas as pd

conn = sqlite3.connect('sample_sales.db')

print("="*60)
print("SAMPLE DATA PREVIEW")
print("="*60)

print("\n1. PRODUCTS:")
df = pd.read_sql_query("SELECT * FROM products", conn)
print(df)

print("\n2. SALESPEOPLE:")
df = pd.read_sql_query("SELECT * FROM salespeople", conn)
print(df)

print("\n3. RECENT SALES (Last 5):")
df = pd.read_sql_query("""
    SELECT 
        s.sale_id,
        c.first_name || ' ' || c.last_name as customer,
        p.product_name,
        sp.first_name || ' ' || sp.last_name as salesperson,
        s.sale_date,
        s.sale_amount,
        s.status
    FROM sales s
    JOIN customers c ON s.customer_id = c.customer_id
    JOIN products p ON s.product_id = p.product_id
    JOIN salespeople sp ON s.salesperson_id = sp.salesperson_id
    ORDER BY s.sale_date DESC
    LIMIT 5
""", conn)
print(df)

print("\n4. SALES BY SALESPERSON (This Month):")
df = pd.read_sql_query("""
    SELECT 
        sp.first_name || ' ' || sp.last_name as salesperson,
        sp.team,
        COUNT(*) as sales_count,
        SUM(s.sale_amount) as total_revenue
    FROM sales s
    JOIN salespeople sp ON s.salesperson_id = sp.salesperson_id
    WHERE s.sale_date >= date('now', 'start of month')
    AND s.status = 'Active'
    GROUP BY sp.salesperson_id
    ORDER BY total_revenue DESC
""", conn)
print(df)

conn.close()
