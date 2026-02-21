"""
Database query tools for the AI agent
These are the "hands" Claude uses to interact with data
"""
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Any

class DatabaseQueryTool:
    def __init__(self, db_path: str = 'sample_sales.db'):
        """
        Initialize the database query tool
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.query_log = []
        
    def query_database(
        self, 
        sql_query: str,
        max_rows: int = 100
    ) -> Dict[str, Any]:
        """
        Execute SQL query and return results
        
        Args:
            sql_query: SQL query to execute
            max_rows: Maximum rows to return (prevents huge results)
            
        Returns:
            {
                'success': bool,
                'row_count': int,
                'columns': list,
                'data': list of dicts,
                'query': str,
                'execution_time': float,
                'message': str
            }
        """
        start_time = datetime.now()
        
        try:
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # This lets us access columns by name
            cursor = conn.cursor()
            
            # Execute query
            cursor.execute(sql_query)
            
            # Get column names
            columns = [description[0] for description in cursor.description] if cursor.description else []
            
            # Fetch results (limit to max_rows)
            rows = cursor.fetchmany(max_rows + 1)
            truncated = len(rows) > max_rows
            if truncated:
                rows = rows[:max_rows]
            
            # Convert to list of dictionaries
            data = []
            for row in rows:
                row_dict = {}
                for col in columns:
                    value = row[col]
                    # Convert any non-JSON-serializable types
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    row_dict[col] = value
                data.append(row_dict)
            
            conn.close()
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Log the query
            self.query_log.append({
                'timestamp': datetime.now().isoformat(),
                'query': sql_query,
                'row_count': len(data),
                'execution_time': execution_time,
                'success': True
            })
            
            result = {
                'success': True,
                'row_count': len(data),
                'columns': columns,
                'data': data,
                'query': sql_query,
                'execution_time': execution_time,
                'truncated': truncated,
                'message': f"Query returned {len(data)} row{'s' if len(data) != 1 else ''}"
            }
            
            if truncated:
                result['message'] += f" (limited to {max_rows}, more rows available)"
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Log failed query
            self.query_log.append({
                'timestamp': datetime.now().isoformat(),
                'query': sql_query,
                'error': str(e),
                'execution_time': execution_time,
                'success': False
            })
            
            return {
                'success': False,
                'query': sql_query,
                'error': str(e),
                'execution_time': execution_time,
                'message': f"Query failed: {str(e)}"
            }
    
    def export_to_excel(
        self, 
        sql_query: str, 
        filepath: str,
        sheet_name: str = 'Data'
    ) -> Dict[str, Any]:
        """
        Execute query and export results to Excel file
        
        Args:
            sql_query: SQL query to execute
            filepath: Path where Excel file will be saved (e.g., 'report.xlsx')
            sheet_name: Name of the worksheet (default: 'Data')
            
        Returns:
            {
                'success': bool,
                'filepath': str,
                'row_count': int,
                'message': str
            }
        """
        import pandas as pd
        
        try:
            # First, run the query to get data
            result = self.query_database(sql_query, max_rows=10000)  # Allow up to 10k rows for export
            
            if not result['success']:
                return result
            
            # Convert to DataFrame
            df = pd.DataFrame(result['data'])
            
            if df.empty:
                return {
                    'success': False,
                    'message': 'Query returned no data to export'
                }
            
            # Add export metadata sheet
            metadata = {
                'Export Date': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                'Query': [sql_query],
                'Row Count': [len(df)],
                'Column Count': [len(df.columns)]
            }
            metadata_df = pd.DataFrame(metadata)
            
            # Write to Excel with multiple sheets
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                metadata_df.to_excel(writer, sheet_name='Export Info', index=False)
                
                # Auto-adjust column widths
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_cells = [cell for cell in column]
                    for cell in column_cells:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
                    worksheet.column_dimensions[column_cells[0].column_letter].width = adjusted_width
            
            return {
                'success': True,
                'filepath': filepath,
                'row_count': len(df),
                'column_count': len(df.columns),
                'message': f'Exported {len(df)} rows to {filepath}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Export failed: {str(e)}'
            }
    
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """
        Get schema information for a specific table
        """
        try:
            # Get table info
            query = f"PRAGMA table_info({table_name})"
            result = self.query_database(query)
            
            if result['success']:
                columns = []
                for row in result['data']:
                    columns.append({
                        'name': row['name'],
                        'type': row['type'],
                        'nullable': not row['notnull']
                    })
                
                # Get sample row
                sample_query = f"SELECT * FROM {table_name} LIMIT 1"
                sample_result = self.query_database(sample_query)
                
                return {
                    'success': True,
                    'table': table_name,
                    'columns': columns,
                    'sample_row': sample_result['data'][0] if sample_result['data'] else None
                }
            else:
                return result
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_tables(self) -> Dict[str, Any]:
        """
        List all tables in the database
        """
        try:
            query = """
            SELECT name 
            FROM sqlite_master 
            WHERE type='table' 
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
            result = self.query_database(query)
            
            if result['success']:
                tables = [row['name'] for row in result['data']]
                return {
                    'success': True,
                    'tables': tables,
                    'count': len(tables)
                }
            else:
                return result
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_query_log(self) -> List[Dict[str, Any]]:
        """
        Return log of all queries executed
        """
        return self.query_log
    
    def export_log(self, filepath: str):
        """
        Export query log to JSON file
        """
        with open(filepath, 'w') as f:
            json.dump(self.query_log, f, indent=2)
        print(f"✓ Query log exported to: {filepath}")

# Test the tool
if __name__ == "__main__":
    print("="*60)
    print("TESTING DATABASE QUERY TOOL (WITH EXCEL EXPORT)")
    print("="*60)
    
    # Create tool
    db_tool = DatabaseQueryTool()
    
    # Test 1: List tables
    print("\n1. Listing all tables:")
    result = db_tool.list_tables()
    if result['success']:
        print(f"   Found {result['count']} tables:")
        for table in result['tables']:
            print(f"   - {table}")
    
    # Test 2: Run a query
    print("\n2. Running query: Top 3 salespeople")
    query = """
    SELECT 
        sp.first_name || ' ' || sp.last_name as salesperson,
        COUNT(*) as sales_count,
        ROUND(SUM(s.sale_amount), 2) as revenue
    FROM sales s
    JOIN salespeople sp ON s.salesperson_id = sp.salesperson_id
    WHERE s.sale_date >= date('now', '-30 days')
    AND s.status = 'Active'
    GROUP BY sp.salesperson_id
    ORDER BY revenue DESC
    LIMIT 3
    """
    result = db_tool.query_database(query)
    if result['success']:
        print(f"   {result['message']}")
        for row in result['data']:
            print(f"   - {row['salesperson']}: {row['sales_count']} sales, ${row['revenue']:,.2f}")
    
    # Test 3: Export to Excel
    print("\n3. Testing Excel export:")
    export_result = db_tool.export_to_excel(
        sql_query=query,
        filepath='test_export.xlsx',
        sheet_name='Top Salespeople'
    )
    if export_result['success']:
        print(f"   ✓ {export_result['message']}")
        print(f"   ✓ File: {export_result['filepath']}")
        print(f"   ✓ Rows: {export_result['row_count']}")
    else:
        print(f"   ✗ Export failed: {export_result.get('error', 'Unknown error')}")
    
    print("\n" + "="*60)
    print("✓ Database query tool with Excel export is working!")
    print("="*60)
