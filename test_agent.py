"""
Quick test of the Q&A agent
"""
from qa_agent import DatabaseQAAgent

print("="*60)
print("TESTING Q&A AGENT")
print("="*60)

# Create agent
agent = DatabaseQAAgent()

# Test questions
test_questions = [
    "How many orders did we have this month?",
    "What is our total revenue?",
    "Which product category has the highest sales?"
]

for i, question in enumerate(test_questions, 1):
    print(f"\n{'='*60}")
    print(f"TEST {i}: {question}")
    print(f"{'='*60}")
    
    answer = agent.ask(question)
    print(f"\nAnswer: {answer}")

print(f"\n{'='*60}")
print("✓ Agent test complete!")
print(f"{'='*60}\n")

# Show query log
agent.show_query_log()
