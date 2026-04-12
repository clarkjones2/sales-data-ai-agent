"""
Test Claude API connection
"""
import os

import anthropic
from dotenv import load_dotenv

# Load .env from the same directory as this script (Python does not read .env automatically)
_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_PROJECT_DIR, ".env"))

_api_key = os.environ.get("ANTHROPIC_API_KEY")
if not _api_key:
    print("✗ ANTHROPIC_API_KEY is not set.")
    print("  Add it to .env as ANTHROPIC_API_KEY=... or export it in your shell.")
    raise SystemExit(1)

# Initialize client
client = anthropic.Anthropic(api_key=_api_key)

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
