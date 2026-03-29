"""
Streamlit Web Interface for AI Database Agent
"""
import os
import streamlit as st
from qa_agent import DatabaseQAAgent
import pandas as pd
import plotly.express as px
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
SUPERSTORE_DB = os.path.join(_PROJECT_DIR, "superstore.db")

# Page config
st.set_page_config(
    page_title="AI Database Assistant",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state (superstore.db: Customers, Locations, Orders, Products, Order_Items)
if 'agent' not in st.session_state:
    st.session_state.agent = DatabaseQAAgent(db_path=SUPERSTORE_DB)
if 'conversation' not in st.session_state:
    st.session_state.conversation = []

# Header
st.title("🤖 AI-Powered Database Assistant")
st.markdown("Ask questions about your data in plain English!")

# Sidebar
with st.sidebar:
    st.header("📊 Quick Stats")
    
    # Get some quick stats
    try:
        result = st.session_state.agent.db_tool.query_database(
            "SELECT COUNT(*) AS total_orders FROM Orders"
        )
        total_orders = result['data'][0]['total_orders'] if result['success'] else 0
        
        result = st.session_state.agent.db_tool.query_database(
            "SELECT COALESCE(SUM(Sales), 0) AS total_revenue FROM Order_Items"
        )
        total_revenue = result['data'][0]['total_revenue'] if result['success'] else 0
        
        st.metric("Total Orders", f"{total_orders:,}")
        st.metric("Total Revenue", f"${total_revenue:,.2f}")
    except:
        st.info("Database stats loading...")
    
    st.markdown("---")
    
    st.header("💡 Example Questions")
    example_questions = [
        "How many orders this month?",
        "Top 5 states by revenue",
        "Sales by product category",
        "Revenue trend last 6 months",
        "Which region has the most sales?"
    ]
    
    for question in example_questions:
        if st.button(question, key=f"ex_{question}"):
            st.session_state.user_input = question
    
    st.markdown("---")
    
    if st.button("🔄 Clear Conversation"):
        st.session_state.conversation = []
        st.session_state.agent.reset_conversation()
        st.rerun()

# Main area
col1, col2 = st.columns([2, 1])

with col1:
    st.header("💬 Ask a Question")
    
    # User input
    user_question = st.text_input(
        "Type your question here:",
        placeholder="e.g., What are the top product categories by revenue?",
        key="question_input"
    )
    
    ask_button = st.button("🚀 Ask", type="primary")
    
    # Process question
    if ask_button and user_question:
        with st.spinner("Agent is thinking..."):
            # Add to conversation
            st.session_state.conversation.append({
                'role': 'user',
                'content': user_question,
                'timestamp': datetime.now()
            })
            
            # Get answer
            answer = st.session_state.agent.ask(user_question)
            
            st.session_state.conversation.append({
                'role': 'agent',
                'content': answer,
                'timestamp': datetime.now()
            })
    
    # Display conversation
    st.markdown("---")
    st.header("📝 Conversation History")
    
    for msg in reversed(st.session_state.conversation[-10:]):  # Show last 10
        if msg['role'] == 'user':
            st.markdown(f"**You:** {msg['content']}")
        else:
            st.markdown(f"**Agent:** {msg['content']}")
        st.caption(msg['timestamp'].strftime('%I:%M %p'))
        st.markdown("---")

with col2:
    st.header("📈 Quick Insights")
    
    # Sales by product chart
    try:
        result = st.session_state.agent.db_tool.query_database("""
            SELECT
                p.Category AS category,
                COUNT(*) AS line_count,
                SUM(oi.Sales) AS revenue
            FROM Order_Items oi
            JOIN Products p ON oi.Product_Key = p.Product_Key
            GROUP BY p.Category
            ORDER BY revenue DESC
        """)
        
        if result['success'] and result['data']:
            df = pd.DataFrame(result['data'])
            
            fig = px.pie(
                df, 
                values='revenue', 
                names='category',
                title='Revenue by Product Category'
            )
            st.plotly_chart(fig, use_container_width=True)
    except:
        st.info("Chart loading...")
    
    # Top regions by revenue (last 30 days)
    try:
        result = st.session_state.agent.db_tool.query_database("""
            SELECT
                l.Region AS name,
                SUM(oi.Sales) AS revenue
            FROM Order_Items oi
            JOIN Orders o ON oi.Order_ID = o.Order_ID
            JOIN Locations l ON o.Location_ID = l.Location_ID
            WHERE o.Order_Date >= date('now', '-30 days')
            GROUP BY l.Region
            ORDER BY revenue DESC
            LIMIT 5
        """)
        
        if result['success'] and result['data']:
            df = pd.DataFrame(result['data'])
            
            fig = px.bar(
                df,
                x='name',
                y='revenue',
                title='Top 5 Regions by Revenue (Last 30 Days)',
                labels={'name': 'Region', 'revenue': 'Revenue'}
            )
            st.plotly_chart(fig, use_container_width=True)
    except:
        st.info("Chart loading...")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>Built with Claude AI 🤖 | Powered by Streamlit ⚡ | Created for Capstone Project 🎓</p>
</div>
""", unsafe_allow_html=True)