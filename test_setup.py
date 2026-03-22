"""
Test script to verify setup
"""
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

print(f"Python version: {sys.version}")

try:
    import anthropic
    print("✓ Anthropic library installed")
except:
    print("✗ Anthropic library NOT installed")

try:
    import pandas
    print("✓ Pandas installed")
except:
    print("✗ Pandas NOT installed")

try:
    import openpyxl
    print("✓ openpyxl installed")
except:
    print("✗ openpyxl NOT installed")

try:
    import pyodbc
    print("✓ pyodbc installed")
except:
    print("⚠ pyodbc NOT installed (OK for Mac)")

import os
if os.environ.get("ANTHROPIC_API_KEY"):
    print("✓ API key is set")
    # Show first/last few characters for confirmation
    key = os.environ.get("ANTHROPIC_API_KEY")
    print(f"  Key: {key[:15]}...{key[-10:]}")
else:
    print("✗ API key NOT set")

print("\nSetup test complete!")
