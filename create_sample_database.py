"""
Create a sample sales database for testing the AI agent
This mimics a vacation sales operation database
"""
import sqlite3
import random
from datetime import datetime, timedelta

def create_database():
    """
    Create SQLite database with sample sales data
    """
    # Connect to database (creates file if doesn't exist)
    conn = sqlite3.connect('sample_sales.db')
    cursor = conn.cursor()
    
    print("Creating database tables...")
    
    # Create tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS customers (
        customer_id INTEGER PRIMARY KEY,
        first_name TEXT,
        last_name TEXT,
        email TEXT,
        phone TEXT,
        lead_source TEXT,
        signup_date DATE,
        customer_type TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY,
        product_name TEXT,
        category TEXT,
        price REAL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS salespeople (
        salesperson_id INTEGER PRIMARY KEY,
        first_name TEXT,
        last_name TEXT,
        hire_date DATE,
        team TEXT,
        manager TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sales (
        sale_id INTEGER PRIMARY KEY,
        customer_id INTEGER,
        product_id INTEGER,
        salesperson_id INTEGER,
        sale_date DATE,
        sale_amount REAL,
        status TEXT,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id),
        FOREIGN KEY (salesperson_id) REFERENCES salespeople(salesperson_id)
    )
    ''')
    
    print("✓ Tables created")
    
    # Sample data
    print("\nInserting sample data...")
    
    # Products
    products = [
        (1, 'Vacation Package A', 'Standard', 2500.00),
        (2, 'Vacation Package B', 'Premium', 4500.00),
        (3, 'Vacation Package C', 'Luxury', 7500.00),
        (4, 'Upgrade Package', 'Upgrade', 1500.00),
        (5, 'Extended Stay', 'Premium', 5500.00)
    ]
    
    cursor.executemany(
        'INSERT OR REPLACE INTO products VALUES (?, ?, ?, ?)',
        products
    )
    print(f"✓ Inserted {len(products)} products")
    
    # Salespeople
    salespeople = [
        (1, 'Sarah', 'Johnson', '2020-01-15', 'Team A', 'Mike Williams'),
        (2, 'John', 'Smith', '2019-03-20', 'Team A', 'Mike Williams'),
        (3, 'Emily', 'Davis', '2021-06-10', 'Team B', 'Lisa Brown'),
        (4, 'Michael', 'Garcia', '2020-11-05', 'Team B', 'Lisa Brown'),
        (5, 'Jessica', 'Martinez', '2022-02-14', 'Team C', 'David Lee'),
        (6, 'David', 'Rodriguez', '2021-08-22', 'Team C', 'David Lee'),
        (7, 'Ashley', 'Wilson', '2020-05-18', 'Team A', 'Mike Williams'),
        (8, 'Chris', 'Anderson', '2021-09-30', 'Team B', 'Lisa Brown')
    ]
    
    cursor.executemany(
        'INSERT OR REPLACE INTO salespeople VALUES (?, ?, ?, ?, ?, ?)',
        salespeople
    )
    print(f"✓ Inserted {len(salespeople)} salespeople")
    
    # Customers
    first_names = ['James', 'Mary', 'Robert', 'Patricia', 'Jennifer', 'Michael', 
                   'Linda', 'William', 'Elizabeth', 'David', 'Barbara', 'Richard',
                   'Susan', 'Joseph', 'Jessica', 'Thomas', 'Sarah', 'Charles']
    
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia',
                  'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez',
                  'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson']
    
    lead_sources = ['Web', 'Phone', 'Referral', 'Direct', 'Email', 'Event']
    customer_types = ['New', 'Returning']
    
    customers = []
    for i in range(1, 501):  # 500 customers
        first = random.choice(first_names)
        last = random.choice(last_names)
        email = f"{first.lower()}.{last.lower()}{i}@email.com"
        phone = f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
        lead_source = random.choice(lead_sources)
        
        # Random date in last 2 years
        days_ago = random.randint(0, 730)
        signup_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        customer_type = random.choice(customer_types)
        
        customers.append((i, first, last, email, phone, lead_source, signup_date, customer_type))
    
    cursor.executemany(
        'INSERT OR REPLACE INTO customers VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        customers
    )
    print(f"✓ Inserted {len(customers)} customers")
    
    # Sales (more recent = more sales)
    print("\nGenerating sales transactions...")
    sales = []
    sale_id = 1
    
    # Generate sales over last 12 months
    for days_ago in range(365, 0, -1):
        sale_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        # More sales on recent days (growing business)
        num_sales = random.randint(2, 8) if days_ago < 90 else random.randint(1, 4)
        
        for _ in range(num_sales):
            customer_id = random.randint(1, 500)
            product_id = random.randint(1, 5)
            salesperson_id = random.randint(1, 8)
            
            # Get product price
            product_price = products[product_id - 1][3]
            
            # Add some variation to price
            sale_amount = round(product_price * random.uniform(0.95, 1.05), 2)
            
            # Most sales are active, some cancelled
            status = random.choices(
                ['Active', 'Cancelled', 'Refunded'],
                weights=[85, 10, 5]
            )[0]
            
            sales.append((sale_id, customer_id, product_id, salesperson_id, 
                         sale_date, sale_amount, status))
            sale_id += 1
    
    cursor.executemany(
        'INSERT OR REPLACE INTO sales VALUES (?, ?, ?, ?, ?, ?, ?)',
        sales
    )
    print(f"✓ Inserted {len(sales)} sales transactions")
    
    # Commit and close
    conn.commit()
    
    # Print summary statistics
    print("\n" + "="*60)
    print("DATABASE SUMMARY")
    print("="*60)
    
    cursor.execute("SELECT COUNT(*) FROM customers")
    print(f"Total Customers: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM products")
    print(f"Total Products: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM salespeople")
    print(f"Total Salespeople: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM sales")
    print(f"Total Sales: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT SUM(sale_amount) FROM sales WHERE status = 'Active'")
    total_revenue = cursor.fetchone()[0]
    print(f"Total Active Revenue: ${total_revenue:,.2f}")
    
    cursor.execute("""
        SELECT COUNT(*) FROM sales 
        WHERE sale_date >= date('now', '-30 days')
    """)
    recent_sales = cursor.fetchone()[0]
    print(f"Sales Last 30 Days: {recent_sales}")
    
    print("\n✓ Database created successfully: sample_sales.db")
    
    conn.close()

if __name__ == "__main__":
    create_database()
