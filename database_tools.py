"""
Database query tools for the AI agent
These are the "hands" Claude uses to interact with data
"""
import os
import re
import shutil
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

def _default_superstore_db_path() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "superstore.db")


def _sqlite_connect(db_path: str, read_only: bool = False) -> sqlite3.Connection:
    """Open SQLite; use URI read-only mode when read_only=True (no accidental writes)."""
    p = Path(os.path.abspath(db_path))
    if read_only:
        uri = p.as_uri() + "?mode=ro"
        return sqlite3.connect(uri, uri=True)
    return sqlite3.connect(str(p))


class DatabaseQueryTool:
    def __init__(self, db_path: Optional[str] = None, read_only: bool = True):
        """
        Initialize the database query tool
        
        Args:
            db_path: Path to SQLite database file (defaults to superstore.db beside this package)
            read_only: If True, open DB in read-only mode (recommended for the agent)
        """
        self.db_path = db_path or _default_superstore_db_path()
        self.read_only = read_only
        self.query_log = []

    def _connect(self) -> sqlite3.Connection:
        return _sqlite_connect(self.db_path, read_only=self.read_only)
        
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
            conn = self._connect()
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

    @staticmethod
    def _normalize_select_sql(sql_query: str) -> str:
        return sql_query.strip().rstrip(";").strip()

    def estimate_select_row_count(self, sql_query: str) -> Dict[str, Any]:
        """
        Return COUNT(*) for a SELECT subquery (how many rows the full query would return).
        """
        s = self._normalize_select_sql(sql_query)
        if not re.match(r"(?is)\s*select\s", s):
            return {
                "success": False,
                "message": "estimate_query_rows only supports a single SELECT statement.",
            }
        wrapped = f"SELECT COUNT(*) AS row_estimate FROM ({s}) AS _subq"
        start = datetime.now()
        try:
            conn = self._connect()
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(wrapped)
            row = cur.fetchone()
            conn.close()
            n = int(row[0]) if row else 0
            elapsed = (datetime.now() - start).total_seconds()
            return {
                "success": True,
                "row_estimate": n,
                "execution_time": elapsed,
                "message": f"Estimated rows: {n:,}",
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Could not estimate rows: {e}",
                "error": str(e),
            }

    def explain_query_plan(self, sql_query: str) -> Dict[str, Any]:
        """SQLite EXPLAIN QUERY PLAN for a SELECT (helps reason about cost)."""
        s = self._normalize_select_sql(sql_query)
        if not re.match(r"(?is)\s*select\s", s):
            return {
                "success": False,
                "message": "explain_query_plan only supports SELECT statements.",
            }
        try:
            conn = self._connect()
            cur = conn.cursor()
            cur.execute(f"EXPLAIN QUERY PLAN {s}")
            rows = cur.fetchall()
            conn.close()
            lines = []
            for r in rows:
                lines.append(
                    {
                        "detail": r[3] if len(r) > 3 else str(r),
                    }
                )
            return {
                "success": True,
                "plan_lines": [x["detail"] for x in lines],
                "raw_rows": len(rows),
                "message": f"EXPLAIN QUERY PLAN returned {len(rows)} line(s)",
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "error": str(e),
            }

    def backup_database(self, backup_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a consistent backup copy using SQLite's backup API (safe vs file copy).
        """
        base = backup_dir or os.path.join(
            os.path.dirname(os.path.abspath(self.db_path)), "backups"
        )
        os.makedirs(base, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest_path = os.path.join(base, f"superstore_backup_{stamp}.db")
        src_conn = None
        dest_conn = None
        try:
            src_conn = sqlite3.connect(self.db_path)
            dest_conn = sqlite3.connect(dest_path)
            src_conn.backup(dest_conn)
            return {
                "success": True,
                "filepath": os.path.abspath(dest_path),
                "message": f"Backup written to {dest_path}",
            }
        except Exception as e:
            return {"success": False, "message": str(e), "error": str(e)}
        finally:
            if dest_conn:
                dest_conn.close()
            if src_conn:
                src_conn.close()
    
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
    print("\n2. Running query: Top 3 customers by revenue (last 30 days)")
    query = """
    SELECT
        c.Customer_Name AS customer,
        COUNT(DISTINCT o.Order_ID) AS order_count,
        ROUND(SUM(oi.Sales), 2) AS revenue
    FROM Order_Items oi
    JOIN Orders o ON oi.Order_ID = o.Order_ID
    JOIN Customers c ON o.Customer_ID = c.Customer_ID
    WHERE o.Order_Date >= date('now', '-30 days')
    GROUP BY c.Customer_ID
    ORDER BY revenue DESC
    LIMIT 3
    """
    result = db_tool.query_database(query)
    if result['success']:
        print(f"   {result['message']}")
        for row in result['data']:
            print(f"   - {row['customer']}: {row['order_count']} orders, ${row['revenue']:,.2f}")
    
    # Test 3: Export to Excel
    print("\n3. Testing Excel export:")
    export_result = db_tool.export_to_excel(
        sql_query=query,
        filepath='test_export.xlsx',
        sheet_name='Top Customers'
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
