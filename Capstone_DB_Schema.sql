-- Superstore schema (SQLite). Matches superstore.db

CREATE TABLE Customers (
    Customer_ID VARCHAR(20) PRIMARY KEY,
    Customer_Name VARCHAR(100),
    Segment VARCHAR(50)
);

CREATE TABLE Locations (
    Location_ID INTEGER PRIMARY KEY,
    Country VARCHAR(50),
    City VARCHAR(100),
    State VARCHAR(100),
    Postal_Code VARCHAR(5),
    Region VARCHAR(50)
);

CREATE TABLE Orders (
    Order_ID VARCHAR(20) PRIMARY KEY,
    Order_Date DATE,
    Ship_Date DATE,
    Ship_Mode VARCHAR(50),
    Customer_ID VARCHAR(20),
    Location_ID INTEGER,
    FOREIGN KEY (Customer_ID) REFERENCES Customers(Customer_ID),
    FOREIGN KEY (Location_ID) REFERENCES Locations(Location_ID)
);

CREATE TABLE Products (
    Product_Key INTEGER PRIMARY KEY,
    Product_ID VARCHAR(30),
    Category VARCHAR(50),
    Sub_Category VARCHAR(50),
    Product_Name VARCHAR(255)
);

CREATE TABLE Order_Items (
    Order_ID VARCHAR(20),
    Product_Key INTEGER,
    Sales DECIMAL(10,2),
    PRIMARY KEY (Order_ID, Product_Key),
    FOREIGN KEY (Order_ID) REFERENCES Orders(Order_ID),
    FOREIGN KEY (Product_Key) REFERENCES Products(Product_Key)
);
