"""
Test script to verify setup
"""
import os
import sys

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

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

if os.environ.get("ANTHROPIC_API_KEY"):
    print("✓ API key is set")
    # Show first/last few characters for confirmation
    key = os.environ.get("ANTHROPIC_API_KEY")
    print(f"  Key: {key[:15]}...{key[-10:]}")
else:
    print("✗ API key NOT set")

print("\nSetup test complete!")
