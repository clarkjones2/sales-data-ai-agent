"""
Natural Language Q&A Agent with Excel Export
Enhanced version with ability to export query results
"""
import anthropic
import os
import json
from database_tools import DatabaseQueryTool
from datetime import datetime

class DatabaseQAAgent:
    def __init__(self, db_path: str = 'sample_sales.db', api_key: str = None):
        """
        Initialize the Q&A agent
        
        Args:
            db_path: Path to SQLite database
            api_key: Anthropic API key (or use ANTHROPIC_API_KEY env var)
        """
        self.client = anthropic.Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY")
        )
        self.db_tool = DatabaseQueryTool(db_path)
        self.conversation_history = []
        
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
        
        # Define tools available to Claude
        tools = [
            {
                "name": "query_database",
                "description": """Execute a SQL query on the sales database to get data.
                
The database contains sales data for a vacation package company with tables:
- customers: Customer information and lead sources
- products: Vacation packages and pricing
- salespeople: Sales team members and their teams
- sales: Individual sales transactions

Use SQLite syntax. Common functions:
- date('now') for current date
- date('now', 'start of month') for first day of current month
- date('now', '-30 days') for 30 days ago
- strftime('%Y-%m', date) for year-month formatting

Always filter active sales with: WHERE status = 'Active'
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
                "name": "export_to_excel",
                "description": """Export query results to an Excel file. Use this when the user asks to 
'export', 'save to excel', 'download', or 'create a spreadsheet'.

The file will be saved with:
- Main sheet containing the query results
- Metadata sheet with export info
- Auto-adjusted column widths
""",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sql_query": {
                            "type": "string",
                            "description": "SQL query to execute and export"
                        },
                        "filepath": {
                            "type": "string",
                            "description": "Filename for the Excel file (e.g., 'sales_report.xlsx')"
                        },
                        "sheet_name": {
                            "type": "string",
                            "description": "Name for the worksheet (default: 'Data')",
                            "default": "Data"
                        }
                    },
                    "required": ["sql_query", "filepath"]
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
            }
        ]
        
        # System prompt with context
        current_date = datetime.now().strftime('%B %d, %Y')
        
        system_prompt = f"""You are a helpful data analyst assistant for a vacation sales company.

Today's date is: {current_date}

{self.schema_context}

When answering questions:
1. Understand what data the user needs
2. Write an appropriate SQL query to get that data
3. Execute the query using the query_database tool
4. Interpret the results
5. Provide a clear, conversational answer

When the user asks to export, save, or download data:
1. Use the export_to_excel tool
2. Create a descriptive filename (e.g., 'sales_report_2026-02.xlsx')
3. Choose an appropriate sheet name
4. Confirm the export location

Important guidelines:
- Be precise with numbers and dates
- Format currency with $ and commas
- If you're not sure, query the data rather than guessing
- Explain any caveats or limitations
 Only include 'Active' status sales unless specifically asked otherwise
- When comparing periods, show both absolute and percentage changes

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
                        elif tool_name == "export_to_excel":
                            result = self.db_tool.export_to_excel(
                                sql_query=tool_input['sql_query'],
                                filepath=tool_input['filepath'],
                                sheet_name=tool_input.get('sheet_name', 'Data')
                            )
                        elif tool_name == "get_table_schema":
                            result = self.db_tool.get_table_schema(
                                tool_input['table_name']
                            )
                        elif tool_name == "list_tables":
                            result = self.db_tool.list_tables()
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
        session_data = {
            'timestamp': datetime.now().isoformat(),
            'conversation': self.conversation_history,
            'queries': self.db_tool.get_query_log()
        }
        
        with open(filepath, 'w') as f:
            json.dump(session_data, f, indent=2, default=str)
        
        print(f"✓ Session exported to: {filepath}\n")

# Command-line interface
if __name__ == "__main__":
    print("="*60)
    print("SALES DATABASE Q&A AGENT (WITH EXCEL EXPORT)")
    print("="*60)
    print("\nI can answer questions about your sales data!")
    print("\n📊 NEW: I can now export results to Excel!")
    print("\nExample questions:")
    print("  • How many sales did we have last month?")
    print("  • Who is our top salesperson?")
    print("  • Export all sales from this month to Excel")
    print("  • Save top 10 salespeople to a spreadsheet")
    print("  • Create an Excel file with Team A performance")
    print("\nCommands:")
    print("  • 'exit' - Quit the program")
    print("  • 'reset' - Start a new conversation")
    print("  • 'log' - Show query history")
    print("="*60 + "\n")
    
    # Create agent
    try:
        agent = DatabaseQAAgent()
        print("✓ Agent initialized successfully!")
        print("✓ Excel export feature enabled!\n")
    except Exception as e:
        print(f"✗ Error initializing agent: {str(e)}")
        print("\nMake sure:")
        print("  1. ANTHROPIC_API_KEY is set")
        print("  2. sample_sales.db exists")
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
