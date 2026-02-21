# Setup Instructions

## Prerequisites

- Python 3.10 or higher
- pip package manager
- Git
- Anthropic API key (see below for how to get one)

## Installation Steps

### 1. Clone the Repository
```bash
git clone https://github.com/clarkjones2/sales-data-ai-agent.git
cd sales-data-ai-agent
```

### 2. Create Virtual Environment

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` at the beginning of your terminal prompt.

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

This will install all required packages including:
- anthropic (Claude AI SDK)
- pandas (data manipulation)
- openpyxl (Excel file generation)
- streamlit (web interface)
- plotly (data visualization)
- python-dotenv (environment variable management)

### 4. Get Your Anthropic API Key

**IMPORTANT: Each team member needs their own API key. Do NOT share API keys.**

1. Go to https://console.anthropic.com/
2. Sign up for a free account (or log in if you already have one)
3. Navigate to "API Keys" in the dashboard
4. Click "Create Key"
5. Give it a name like "Sales Data AI Agent"
6. Copy the key (it starts with `sk-ant-api03-...`)
7. **Save it somewhere safe - you'll only see it once!**

### 5. Configure Your API Key

Create a `.env` file in the project root directory:
```bash
echo "ANTHROPIC_API_KEY=your-actual-api-key-here" > .env
```

Or create it manually:
1. Create a new file called `.env` (note the dot at the beginning)
2. Add this single line: `ANTHROPIC_API_KEY=sk-ant-api03-your-key-here`
3. Replace `sk-ant-api03-your-key-here` with your actual API key
4. Save the file

**SECURITY NOTE:** 
- Never commit your `.env` file to Git
- Never share your API key with others
- The `.env` file is already in `.gitignore` to prevent accidental commits

### 6. Generate Sample Database
```bash
python3 create_sample_database.py
```

This creates `sample_sales.db` with realistic sample data:
- 500 customers
- 5 products
- 8 salespeople
- ~1,100 sales transactions

You should see output confirming the database was created successfully.

### 7. Verify Installation

Run the test scripts to confirm everything is working:
```bash
python3 test_setup.py
python3 test_claude.py
```

Both should show success messages with green checkmarks.

## Running the Application

### Option 1: Command-Line Interface
```bash
python3 qa_agent_with_excel.py
```

This starts an interactive session where you can ask questions like:
- "How many sales did we have this month?"
- "Who is our top salesperson?"
- "Export top 10 salespeople to Excel"

Type `exit` to quit.

### Option 2: Web Interface (Recommended)
```bash
streamlit run web_app.py
```

This opens a web browser automatically at `http://localhost:8501` with a modern dashboard interface.

## Understanding Claude API Costs

### How the API Works

The Claude API is a pay-per-use service. You are charged based on:
- **Input tokens:** The text you send to Claude (your questions + context)
- **Output tokens:** The text Claude generates in response

Approximate costs (as of 2024):
- Claude Sonnet: ~$3 per million input tokens, ~$15 per million output tokens
- A typical question + response uses 500-2,000 tokens
- **Estimated cost per query:** $0.01 - $0.03

### Free Credits

New Anthropic accounts typically receive $5 in free credits, which is enough for:
- Approximately 150-500 queries depending on complexity
- Several hours of testing and development
- Completing this project if used efficiently

### Checking Your Credits

1. Go to https://console.anthropic.com/
2. Log in to your account
3. Look at the top-right corner or dashboard
4. You'll see your current credit balance and usage

### Managing Costs

**Best Practices:**
- Use caching (our agent automatically does this for repeated queries)
- Test with simple queries first
- Don't spam the API during testing
- Share test results with team rather than everyone running the same tests
- Monitor your usage weekly

**Budget Guidelines:**
- Individual development: $5-10/month is typical
- Team of 4 sharing tests: $10-20/month total
- If costs are a concern, reach out to Anthropic support for educational credits

### Do I Share My API Key?

**NO! Each person should have their own API key.**

Reasons:
- **Security:** If one key is compromised, only one account is affected
- **Cost tracking:** You can see your own usage and costs
- **Rate limits:** Each key has its own rate limits
- **Accountability:** Credits come from individual accounts

**For Team Collaboration:**
- Each team member gets their own free $5 credits
- Total team budget: $20 in free credits (4 members × $5 each)
- Each person pays for their own usage after free credits
- No need to pool money or share keys

## Troubleshooting

### "Command not found: python3"
**Solution:** Try using `python` instead of `python3`

### "No module named 'anthropic'"
**Solution:** 
1. Make sure virtual environment is activated (you should see `(venv)`)
2. Run `pip install -r requirements.txt` again

### "Could not resolve authentication method"
**Solution:**
1. Check that `.env` file exists in project root
2. Verify API key is correct (no extra quotes or spaces)
3. Make sure key starts with `sk-ant-api03-`

### "Error code: 401 - Invalid API key"
**Solution:**
1. Verify you copied the entire API key
2. Generate a new key in Anthropic console
3. Update your `.env` file

### "Error code: 429 - Rate limit exceeded"
**Solution:**
1. You're making too many requests too quickly
2. Wait a few minutes and try again
3. Implement longer delays between requests

### "No such file or directory: sample_sales.db"
**Solution:** Run `python3 create_sample_database.py` first

### Web interface shows blank page
**Solution:**
1. Check terminal for error messages
2. Make sure Streamlit installed: `pip install streamlit`
3. Try clearing browser cache
4. Access directly at `http://localhost:8501`

### "ModuleNotFoundError: No module named 'dotenv'"
**Solution:** Install python-dotenv: `pip install python-dotenv`

## Project Structure
```
sales-data-ai-agent/
├── README.md                      # Project overview
├── SETUP.md                       # This file
├── requirements.txt               # Python dependencies
├── .env                           # Your API key (DO NOT COMMIT)
├── .gitignore                     # Git ignore rules
│
├── create_sample_database.py      # Generates sample data
├── database_tools.py              # Database query engine
├── qa_agent.py                    # Core AI agent
├── qa_agent_with_excel.py         # Agent with Excel export
├── web_app.py                     # Streamlit web interface
│
├── sample_sales.db                # Generated sample database
├── test_agent.py                  # Tests
├── test_setup.py                  # Setup verification
└── test_claude.py                 # API verification
```

## Getting Help

If you encounter issues:

1. Check this SETUP.md file first
2. Review the Troubleshooting section above
3. Check the main README.md for project overview
4. Open an issue on GitHub with:
   - What you were trying to do
   - The exact error message
   - Your operating system
   - Python version (`python --version`)

## Next Steps

Once everything is running:

1. Try asking the agent simple questions to get familiar
2. Explore the web interface features
3. Review the code to understand how it works
4. Read the main README.md for architecture details

## Security Reminders

- ✅ Each person uses their own API key
- ✅ Keep your `.env` file private
- ✅ Never commit `.env` to Git
- ✅ Never share your API key in chat/email
- ✅ Regenerate your key if you accidentally expose it
