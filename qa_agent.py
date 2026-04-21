"""
Natural Language Q&A Agent for Database Queries
This agent uses Claude to understand questions and query the database
"""
import anthropic
import json
import os
from datetime import datetime
from typing import Optional
from visualization_tools import VisualizationTool
from visualization_tools import CREATE_VISUALIZATION_TOOL_SPEC

from dotenv import load_dotenv

from agent_analysis_tools import (
    BACKUP_DATABASE_TOOL,
    ESTIMATE_QUERY_ROWS_TOOL,
    EXPLAIN_QUERY_PLAN_TOOL,
    RUN_DATA_QUALITY_TOOL,
)
from conversation_export import build_json_export, conversation_to_markdown, conversation_to_pdf_bytes
from data_quality import format_data_quality_markdown, run_data_quality_report
from database_tools import DatabaseQueryTool
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database schema definition (from llm_prompts.py)
DATABASE_SCHEMA_PROMPT = """
You are a SQL Generator for a SQLite Database.

The schema is as follows. There are notes about each table:

customers(customer_id, customer_name, segment)
-Primary key is customer_id.
-Each record represents a unique customer ID

products(product_key, product_id, category, sub_category, product_name)
-Primary key is product_key
-Each record represents a unique product

locations(location_id, country, city, state, postal_code, region)
-Primary key is location_id
-Each recrod represents a unique location

orders(order_id, order_date, ship_date, ship_mode, customer_id, location_id)
-Primary key is order_id
-customer_id is a foreign key -> customers.customer_id
-location_id is a foreing key -> locations.location_id
-Each record represents a unique order placed by a customer and associated with a shipping location

order_items(order_id, product_key, sales)
-order_id and product_key are a composite primary key
-order_id -> orders.order_id
-product_key -> products.product_key
-Each record represents a product included in a specific order.

Functional Dependencies
Customer_ID → Customer_Name, Segment
Product_Key → Product_ID , Category, Sub_Category, Product_Name
Location_ID → Country, City, State, Postal_Code, Region
Order_ID → Order_Date, Ship_Date, Ship_Mode, Customer_ID, Location_ID
(Order_ID, Product_Key) → Sales

Entity Relationships
Customers (1) —— (Many) Orders
Orders (1) —— (Many) Order_Items
Products (1) —— (Many) Order_Items
Locations (1) —— (Many) Orders

"""

class DatabaseQAAgent:
    def __init__(
        self,
        db_path: Optional[str] = None,
        api_key: str = None,
        read_only: bool = True,
    ):
        """
        Initialize the Q&A agent
        
        Args:
            db_path: Path to SQLite database (defaults to superstore.db next to database_tools.py)
            api_key: Anthropic API key (or use ANTHROPIC_API_KEY env var)
            read_only: Open SQLite in read-only mode (recommended)
        """
        self.client = anthropic.Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY")
        )
        self.db_tool = DatabaseQueryTool(db_path, read_only=read_only)
        self.viz_tool = VisualizationTool(self.db_tool)
        self.conversation_history = []
        self.last_chart_exports: list = []
        self.last_png_exports: list = []
        self.last_query_data = None  # Track the latest data

        # Get database schema for context
        self.schema_context = self._build_schema_context()
        
    def _build_schema_context(self) -> str:
        """
        Build a description of the database schema for Claude
        """
        context = "# Database Schema\n\n"
        
        # Get all tables
        tables_result = self.db_tool.list_tables()
        if not tables_result['success']:
            return "Database schema unavailable"
        
        # For each table, get its schema
        for table_name in tables_result['tables']:
            schema_result = self.db_tool.get_table_schema(table_name)
            if schema_result['success']:
                context += f"## Table: {table_name}\n"
                context += "Columns:\n"
                for col in schema_result['columns']:
                    context += f"  - {col['name']} ({col['type']})\n"
                
                # Add sample row if available
                if schema_result['sample_row']:
                    context += "\nSample row:\n"
                    context += f"  {json.dumps(schema_result['sample_row'], indent=2)}\n"
                context += "\n"
        
        return context
    
    def ask(self, question: str) -> str:
        """
        Ask a question about the data
        
        Args:
            question: Natural language question
            
        Returns:
            Natural language answer
        """
        # Add user question to history
        self.conversation_history.append({
            "role": "user",
            "content": question
        })

        self.last_chart_exports = []
        self.last_png_exports = []
        self.last_query_data = None  # Reset data for each new question

        # Define tools available to Claude
        tools = [
            {
                "name": "query_database",
                "description": """Execute a SQL query on the Superstore database to get data.

Tables (SQLite):
- Customers: Customer_ID, Customer_Name, Segment
- Locations: Location_ID, Country, City, State, Postal_Code, Region
- Orders: Order_ID, Order_Date, Ship_Date, Ship_Mode, Customer_ID, Location_ID
- Products: Product_Key (PK), Product_ID, Category, Sub_Category, Product_Name
- Order_Items: Order_ID, Product_Key, Sales (line revenue; join Orders and Products for context)

Use SQLite syntax. Common functions:
- date('now') for current date
- date('now', 'start of month') for first day of current month
- date('now', '-30 days') for 30 days ago
- strftime('%Y-%m', Order_Date) for year-month formatting

Line revenue is in Order_Items.Sales. Join Order_Items to Orders on Order_ID, and to Products on Product_Key.
""",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sql_query": {
                            "type": "string",
                            "description": "SQL query to execute (SQLite syntax)"
                        }
                    },
                    "required": ["sql_query"]
                }
            },
            {
                "name": "get_table_schema",
                "description": "Get the structure and column information for a specific table",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "Name of the table"
                        }
                    },
                    "required": ["table_name"]
                }
            },
            {
                "name": "list_tables",
                "description": "List all tables in the database",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            },
            CREATE_VISUALIZATION_TOOL_SPEC,
            #LIST_SAVED_REPORTS_TOOL,
            #RUN_SAVED_REPORT_TOOL,
            ESTIMATE_QUERY_ROWS_TOOL,
            EXPLAIN_QUERY_PLAN_TOOL,
            RUN_DATA_QUALITY_TOOL,
            BACKUP_DATABASE_TOOL,
        ]
        
        # System prompt with context
        current_date = datetime.now().strftime('%B %d, %Y')
        
        system_prompt = f"""You are a helpful data analyst assistant for retail Superstore order and sales data.

Today's date is: {current_date}

{self.schema_context}

When answering questions:
1. Understand what data the user needs
2. Write an appropriate SQL query to get that data
3. Execute the query using the query_database tool (or create_visualization when they want a chart)
4. Interpret the results
5. Provide a clear, conversational answer

When the user asks for a chart, graph, plot, or visualization:
1. Write SQL that returns aggregated rows with clear column aliases (e.g. category, order_count, revenue).
2. Call create_visualization with matching chart_type and x_column / y_column names exactly as in the SELECT.
3. Tell the user where the HTML file was saved and briefly what the chart shows.

Important guidelines:
- Be precise with numbers and dates
- Format currency with $ and commas
- If you're not sure, query the data rather than guessing
- Explain any caveats or limitations
- Revenue for a line item is Order_Items.Sales; total order or customer revenue sums Order_Items.Sales across joined rows
- When comparing periods, show both absolute and percentage changes when helpful
- Trust & citations: When stating metrics, briefly cite the source (e.g. "from query_database on aggregated Order_Items" or "saved report revenue_by_category"). If you used estimate_query_rows, mention the approximate row count before interpreting large results.
- Use list_saved_reports / run_saved_report when the user wants a standard or reusable report. Use estimate_query_rows before very large SELECTs. Use run_data_quality_checks when asked about data quality. Use backup_database only when the user explicitly wants a backup file.

Keep your answers conversational and helpful, not overly technical.
"""
        
        # Call Claude with tools - allow multiple iterations for complex questions
        max_iterations = 10
        
        for iteration in range(max_iterations):
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=system_prompt,
                tools=tools,
                messages=self.conversation_history
            )
            
            # Check if Claude is done
            if response.stop_reason == "end_turn":
                # Extract final answer
                answer = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        answer = block.text
                
                # Add to conversation history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": answer
                })
                
                return answer
            
            # Execute tool calls
            if response.stop_reason == "tool_use":
                # Add Claude's response to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response.content
                })
                
                # Execute each tool
                tool_results = []
                
                for block in response.content:
                    if block.type == "tool_use":
                        tool_name = block.name
                        tool_input = block.input
                        
                        # Execute the appropriate tool
                        if tool_name == "query_database":
                            result = self.db_tool.query_database(
                                tool_input['sql_query']
                            )
                            # Capture the raw rows returned by the query
                            if result.get("success") and result.get("data"):
                                self.last_query_data = result["data"]

                        elif tool_name == "get_table_schema":
                            result = self.db_tool.get_table_schema(
                                tool_input['table_name']
                            )
                        elif tool_name == "list_tables":
                            result = self.db_tool.list_tables()
                        elif tool_name == "create_visualization":
                            result = self.viz_tool.create_visualization(
                                sql_query=tool_input["sql_query"],
                                chart_type=tool_input["chart_type"],
                                x_column=tool_input["x_column"],
                                y_column=tool_input["y_column"],
                                title=tool_input.get("title") or "",
                                color_column=tool_input.get("color_column") or None,
                            )
                            if result.get("success") and result.get("filepath"):
                                self.last_chart_exports.append(result["filepath"])
                            if result.get("png_filepath"):
                                self.last_png_exports.append(result["png_filepath"])
                        elif tool_name == "list_saved_reports":
                            result = {
                                "success": True,
                                "reports": list_saved_reports(),
                            }
                        elif tool_name == "run_saved_report":
                            rid = tool_input["report_id"]
                            sql = get_report_sql(rid)
                            if not sql:
                                result = {
                                    "success": False,
                                    "message": f"Unknown report_id: {rid}",
                                }
                            else:
                                result = self.db_tool.query_database(sql)
                                result["saved_report_id"] = rid
                                # Capture the data if they run a saved report
                                if result.get("success") and result.get("data"):
                                    self.last_query_data = result["data"]

                        elif tool_name == "estimate_query_rows":
                            result = self.db_tool.estimate_select_row_count(
                                tool_input["sql_query"]
                            )
                        elif tool_name == "explain_query_plan":
                            result = self.db_tool.explain_query_plan(
                                tool_input["sql_query"]
                            )
                        elif tool_name == "run_data_quality_checks":
                            dq = run_data_quality_report(self.db_tool.db_path)
                            if dq.get("success"):
                                dq["markdown_summary"] = format_data_quality_markdown(
                                    dq
                                )
                            result = dq
                        elif tool_name == "backup_database":
                            bdir = tool_input.get("backup_directory") or None
                            result = self.db_tool.backup_database(
                                backup_dir=bdir
                            )
                        else:
                            result = {'error': f'Unknown tool: {tool_name}'}
                        
                        # Add result to tool_results
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result, default=str)
                        })
                
                # Add tool results to conversation
                self.conversation_history.append({
                    "role": "user",
                    "content": tool_results
                })
        
        return "I apologize, but I reached the maximum number of steps trying to answer your question. Please try rephrasing it or breaking it into smaller questions."
    
    def reset_conversation(self):
        """Clear conversation history (start fresh)"""
        self.conversation_history = []
        self.last_chart_exports = []
        self.last_png_exports = []
        self.last_query_data = None  # Clear the cache
        print("Conversation reset.\n")
    
    def show_query_log(self):
        """Display recent queries executed"""
        queries = self.db_tool.get_query_log()
        if not queries:
            print("No queries executed yet.\n")
            return
        
        print(f"\n{'='*60}")
        print(f"QUERY LOG ({len(queries)} queries)")
        print(f"{'='*60}")
        for i, q in enumerate(queries[-10:], 1):  # Show last 10
            status = "✓" if q['success'] else "✗"
            print(f"\n{status} Query {i} ({q['execution_time']:.3f}s):")
            print(f"   {q['query'][:100]}{'...' if len(q['query']) > 100 else ''}")
            if not q['success']:
                print(f"   Error: {q.get('error', 'Unknown error')}")
        print(f"\n{'='*60}\n")
    
    def export_session(self, filepath: str = 'session_log.json'):
        """Export conversation and query log to file"""
        payload = build_json_export(
            self.conversation_history,
            self.db_tool.get_query_log(),
            self.last_chart_exports,
        )
        with open(filepath, 'w') as f:
            json.dump(payload, f, indent=2, default=str)

        print(f"✓ Session exported to: {filepath}\n")

    def export_session_markdown(self, filepath: str = "session_log.md") -> None:
        """Write conversation + query log as Markdown."""
        md = conversation_to_markdown(
            self.conversation_history,
            self.db_tool.get_query_log(),
        )
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"✓ Markdown exported to: {filepath}\n")

    def export_session_pdf(self, filepath: str = "session_log.pdf") -> None:
        """Write a simple PDF of the Markdown export."""
        md = conversation_to_markdown(
            self.conversation_history,
            self.db_tool.get_query_log(),
        )
        pdf_bytes = conversation_to_pdf_bytes(md)
        with open(filepath, "wb") as f:
            f.write(pdf_bytes)
        print(f"✓ PDF exported to: {filepath}\n")

# Command-line interface
if __name__ == "__main__":
    print("="*60)
    print("SALES DATABASE Q&A AGENT")
    print("="*60)
    print("\nI can answer questions about your sales data!")
    print("\nExample questions:")
    print("  • How many orders were placed last month?")
    print("  • What is our total revenue?")
    print("  • Show sales by product category")
    print("  • Which region has the highest revenue?")
    print("  • Top customers by spend")
    print("  • Bar chart of revenue by product category")
    print("\nCommands:")
    print("  • 'exit' - Quit the program")
    print("  • 'reset' - Start a new conversation")
    print("  • 'log' - Show query history")
    print("="*60 + "\n")
    
    # Create agent
    try:
        agent = DatabaseQAAgent()
        print("✓ Agent initialized successfully!\n")
    except Exception as e:
        print(f"✗ Error initializing agent: {str(e)}")
        print("\nMake sure:")
        print("  1. ANTHROPIC_API_KEY is set")
        print("  2. superstore.db exists")
        exit(1)
    
    # Main loop
    while True:
        try:
            question = input("You: ").strip()
            
            if not question:
                continue
                
            if question.lower() == 'exit':
                # Export session before exiting
                agent.export_session()
                print("Goodbye! 👋\n")
                break
                
            if question.lower() == 'reset':
                agent.reset_conversation()
                continue
                
            if question.lower() == 'log':
                agent.show_query_log()
                continue
            
            # Get answer from agent
            print("\n[Agent is thinking...]\n")
            answer = agent.ask(question)
            print(f"Agent: {answer}\n")
            
        except KeyboardInterrupt:
            print("\n\nInterrupted. Exiting...\n")
            agent.export_session()
            break
        except Exception as e:
            print(f"\n✗ Error: {str(e)}\n")