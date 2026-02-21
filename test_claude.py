"""
Test Claude API connection
"""
import anthropic
import os

# Initialize client
client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY")
)

# Send a simple test message
print("Testing Claude API connection...")

try:
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=100,
        messages=[{
            "role": "user",
            "content": "Say 'API connection successful!' if you can read this."
        }]
    )
    
    # Print response
    response_text = message.content[0].text
    print(f"\nClaude says: {response_text}")
    print("\n✓ API test successful!")
    
except Exception as e:
    print(f"\n✗ API test failed: {str(e)}")
