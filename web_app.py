"""
Streamlit Web Interface for AI Database Agent
"""
import streamlit as st
from qa_agent import DatabaseQAAgent
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
# Page config
st.set_page_config(
    page_title="AI Database Assistant",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
if 'agent' not in st.session_state:
    st.session_state.agent = DatabaseQAAgent()
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
            "SELECT COUNT(*) as total_sales FROM sales WHERE status = 'Active'"
        )
        total_sales = result['data'][0]['total_sales'] if result['success'] else 0
        
        result = st.session_state.agent.db_tool.query_database(
            "SELECT SUM(sale_amount) as total_revenue FROM sales WHERE status = 'Active'"
        )
        total_revenue = result['data'][0]['total_revenue'] if result['success'] else 0
        
        st.metric("Total Active Sales", f"{total_sales:,}")
        st.metric("Total Revenue", f"${total_revenue:,.2f}")
    except:
        st.info("Database stats loading...")
    
    st.markdown("---")
    
    st.header("💡 Example Questions")
    example_questions = [
        "How many sales this month?",
        "Top 5 salespeople",
        "Sales by product category",
        "Revenue trend last 6 months",
        "Team performance comparison"
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
        placeholder="e.g., Who are the top salespeople this month?",
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
                p.category,
                COUNT(*) as sales_count,
                SUM(s.sale_amount) as revenue
            FROM sales s
            JOIN products p ON s.product_id = p.product_id
            WHERE s.status = 'Active'
            GROUP BY p.category
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
    
    # Top salespeople
    try:
        result = st.session_state.agent.db_tool.query_database("""
            SELECT 
                sp.first_name || ' ' || sp.last_name as name,
                SUM(s.sale_amount) as revenue
            FROM sales s
            JOIN salespeople sp ON s.salesperson_id = sp.salesperson_id
            WHERE s.status = 'Active'
            AND s.sale_date >= date('now', '-30 days')
            GROUP BY sp.salesperson_id
            ORDER BY revenue DESC
            LIMIT 5
        """)
        
        if result['success'] and result['data']:
            df = pd.DataFrame(result['data'])
            
            fig = px.bar(
                df,
                x='name',
                y='revenue',
                title='Top 5 Salespeople (Last 30 Days)',
                labels={'name': 'Salesperson', 'revenue': 'Revenue'}
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