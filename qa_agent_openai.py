"""
Natural Language Q&A Agent for Database Queries
This agent uses OpenAI to understand questions and query the database
"""
import openai
import os
import json
from typing import Optional
from database_tools import DatabaseQueryTool
from datetime import datetime

class DatabaseQAAgent:
    def __init__(self, db_path: Optional[str] = None, api_key: str = None, model: str = "gpt-4o"):
        """
        Initialize the Q&A agent
        
        Args:
            db_path: Path to SQLite database (defaults to superstore.db next to database_tools.py)
            api_key: OpenAI API key (or use OPENAI_API_KEY env var)
            model: OpenAI model to use (default: gpt-4o)
        """
        self.client = openai.OpenAI(
            api_key=api_key or os.environ.get("OPENAI_API_KEY")
        )
        self.model = model
        self.db_tool = DatabaseQueryTool(db_path)
        self.conversation_history = []
        
        # Get database schema for context
        self.schema_context = self._build_schema_context()
        
    def _build_schema_context(self) -> str:
        """
        Build a description of the database schema for the model
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
        
        # Define tools available to the model (OpenAI format)
        tools = [
            {
                "type": "function",
                "function": {
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
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sql_query": {
                                "type": "string",
                                "description": "SQL query to execute (SQLite syntax)"
                            }
                        },
                        "required": ["sql_query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_table_schema",
                    "description": "Get the structure and column information for a specific table",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "description": "Name of the table"
                            }
                        },
                        "required": ["table_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_tables",
                    "description": "List all tables in the database",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            }
        ]
        
        # System prompt with context
        current_date = datetime.now().strftime('%B %d, %Y')
        
        system_prompt = f"""You are a helpful data analyst assistant for retail Superstore order and sales data.

Today's date is: {current_date}

{self.schema_context}

When answering questions:
1. Understand what data the user needs
2. Write an appropriate SQL query to get that data
3. Execute the query using the query_database tool
4. Interpret the results
5. Provide a clear, conversational answer

Important guidelines:
- Be precise with numbers and dates
- Format currency with $ and commas
- If you're not sure, query the data rather than guessing
- Explain any caveats or limitations
- Revenue for a line item is Order_Items.Sales; total order or customer revenue sums Order_Items.Sales across joined rows
- When comparing periods, show both absolute and percentage changes when helpful

Keep your answers conversational and helpful, not overly technical.
"""
        
        # Build messages list with system prompt (OpenAI uses a system message)
        messages = [{"role": "system", "content": system_prompt}] + self.conversation_history
        
        # Call OpenAI with tools - allow multiple iterations for complex questions
        max_iterations = 10
        
        for iteration in range(max_iterations):
            # Newer models (gpt-5+, gpt-4.1+) use max_completion_tokens
            _newer = any(tag in self.model for tag in ["gpt-5", "gpt-4.1"])
            token_param = {"max_completion_tokens": 4096} if _newer else {"max_tokens": 4096}

            response = self.client.chat.completions.create(
                model=self.model,
                **token_param,
                tools=tools,
                messages=messages
            )
            
            choice = response.choices[0]
            
            # Check if the model is done
            if choice.finish_reason == "stop":
                # Extract final answer
                answer = choice.message.content or ""
                
                # Add to conversation history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": answer
                })
                
                return answer
            
            # Execute tool calls
            if choice.finish_reason == "tool_calls":
                # Add the assistant's response (with tool calls) to messages
                messages.append(choice.message)
                
                # Also add to conversation history for consistency
                self.conversation_history.append({
                    "role": "assistant",
                    "content": choice.message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in choice.message.tool_calls
                    ]
                })
                
                # Execute each tool
                for tool_call in choice.message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_input = json.loads(tool_call.function.arguments)
                    
                    # Execute the appropriate tool
                    if tool_name == "query_database":
                        result = self.db_tool.query_database(
                            tool_input['sql_query']
                        )
                    elif tool_name == "get_table_schema":
                        result = self.db_tool.get_table_schema(
                            tool_input['table_name']
                        )
                    elif tool_name == "list_tables":
                        result = self.db_tool.list_tables()
                    else:
                        result = {'error': f'Unknown tool: {tool_name}'}
                    
                    # Add tool result to messages (OpenAI format)
                    tool_result_message = {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, default=str)
                    }
                    messages.append(tool_result_message)
        
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
    print("SALES DATABASE Q&A AGENT (OpenAI)")
    print("="*60)
    print("\nI can answer questions about your sales data!")
    print("\nExample questions:")
    print("  • How many orders were placed last month?")
    print("  • What is our total revenue?")
    print("  • Show sales by product category")
    print("  • Which region has the highest revenue?")
    print("  • Top customers by spend")
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
        print("  1. OPENAI_API_KEY is set")
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
