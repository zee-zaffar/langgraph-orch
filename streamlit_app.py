import asyncio
import streamlit as st
import sys
import os
from pathlib import Path

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# Import from the graph-chat-agent file using importlib
import importlib.util
spec = importlib.util.spec_from_file_location("graph_chat_agent", current_dir / "graph-chat-agent.py")
graph_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(graph_module)

# Now we can use the functions
create_graph = graph_module.create_graph
get_mcp_tools = graph_module.get_mcp_tools

from langchain_core.messages import HumanMessage, AIMessage
import time

# Configure Streamlit page
st.set_page_config(
    page_title="LangGraph Chat Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .stChatMessage[data-testid="user-message"] {
        background-color: #f0f2f6;
        border-left: 4px solid #1f77b4;
    }
    .stChatMessage[data-testid="assistant-message"] {
        background-color: #e8f5e8;
        border-left: 4px solid #2ca02c;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'graph' not in st.session_state:
    st.session_state.graph = None
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'thread_id' not in st.session_state:
    st.session_state.thread_id = "streamlit-session-1"
if 'config' not in st.session_state:
    st.session_state.config = {"configurable": {"thread_id": st.session_state.thread_id}}
if 'mcp_tools_info' not in st.session_state:
    st.session_state.mcp_tools_info = []

async def initialize_graph():
    """Initialize the LangGraph instance"""
    if st.session_state.graph is None:
        with st.spinner("🔧 Initializing LangGraph and MCP tools..."):
            try:
                # Get MCP tools info for display
                mcp_tools = await get_mcp_tools()
                st.session_state.mcp_tools_info = [
                    {"name": tool.name, "description": tool.description} 
                    for tool in mcp_tools
                ]
                
                # Create the graph
                st.session_state.graph = await create_graph()
                st.success("✅ LangGraph initialized successfully!")
                return True
            except Exception as e:
                st.error(f"❌ Failed to initialize LangGraph: {e}")
                return False
    return True

async def process_message(user_input):
    """Process user message through the graph"""
    if not st.session_state.graph:
        st.error("Graph not initialized. Please refresh the page.")
        return None
    
    try:
        # Add user message to conversation history
        st.session_state.conversation_history.append(HumanMessage(content=user_input))
        
        # Invoke the graph
        with st.spinner("🔄 Processing..."):
            response = await st.session_state.graph.ainvoke(
                {"messages": st.session_state.conversation_history},
                config=st.session_state.config
            )
        
        # Update conversation history with full response
        st.session_state.conversation_history = response["messages"]
        
        # Return the latest AI response
        return response["messages"][-1]
        
    except Exception as e:
        st.error(f"❌ Error processing message: {e}")
        return None

def display_message(message, is_user=False):
    """Display a chat message with proper styling"""
    if is_user:
        # User message styling
        with st.chat_message("user"):
            st.markdown("You:")
            st.write(message.content)
    else:
        # Assistant message styling 
        with st.chat_message("assistant"):
            st.markdown("AI Assistant:")
            st.write(message.content)
            
            # Show tool usage if it's an AI message with tool calls
            if hasattr(message, 'tool_calls') and message.tool_calls:
                tool_names = [call.get('name', 'Unknown') for call in message.tool_calls]
                st.success(f"🔧 **Tools used:** {', '.join(tool_names)}")

def main():
    """Main Streamlit application"""
    
    # Header
    st.title("🤖 LangGraph Chat Agent")
    st.markdown("---")
    
    # Sidebar with information
    with st.sidebar:
        st.header("ℹ️ Information")
        
        # Initialize graph button
        if st.button("🔄 Initialize/Restart Graph"):
            st.session_state.graph = None
            st.session_state.conversation_history = []
            st.session_state.mcp_tools_info = []
            st.rerun()
        
        # Show available tools
        if st.session_state.mcp_tools_info:
            st.subheader("🔧 Available MCP Tools")
            for tool in st.session_state.mcp_tools_info:
                with st.expander(f"📌 {tool['name']}"):
                    st.write(tool['description'])
        
        # Built-in tools
        st.subheader("🏠 Built-in Tools")
        with st.expander("💰 Mortgage Calculator"):
            st.write("Calculate monthly mortgage payments and totals")
        
        # Session info
        st.subheader("📊 Session Info")
        st.write(f"**Thread ID:** {st.session_state.thread_id}")
        st.write(f"**Messages:** {len(st.session_state.conversation_history)}")
        
        # Clear conversation
        if st.button("🗑️ Clear Conversation"):
            st.session_state.conversation_history = []
            st.rerun()
    
    # Main chat interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("💬 Chat")
        
        # Initialize graph on first run
        if asyncio.run(initialize_graph()):
            
            # Chat container
            chat_container = st.container()
            
            # Display conversation history
            with chat_container:
                for i, message in enumerate(st.session_state.conversation_history):
                    if isinstance(message, HumanMessage):
                        display_message(message, is_user=True)
                    elif isinstance(message, AIMessage):
                        display_message(message, is_user=False)
            
            # Input form
            with st.form(key="chat_form", clear_on_submit=True):
                user_input = st.text_input(
                    "Type your message:",
                    placeholder="Ask me anything... (e.g., 'What's the weather in Paris?' or 'Calculate 15 + 27')",
                    key="user_input"
                )
                
                col_send, col_example = st.columns([1, 2])
                with col_send:
                    submit_button = st.form_submit_button("Send 📤")
                
                with col_example:
                    if st.form_submit_button("💡 Try Example"):
                        user_input = "What's the weather in London?"
                        submit_button = True
            
            # Process message when submitted
            if submit_button and user_input.strip():
                # Display user message immediately
                display_message(HumanMessage(content=user_input), is_user=True)
                
                # Process and display AI response
                ai_response = asyncio.run(process_message(user_input))
                if ai_response:
                    display_message(ai_response, is_user=False)
                
                # Rerun to update the interface
                st.rerun()
    
    with col2:
        st.subheader("📋 Quick Actions")
        
        # Predefined example buttons
        if st.button("🌤️ Weather Query"):
            example_input = "What's the weather in New York?"
            st.session_state.conversation_history.append(HumanMessage(content=example_input))
            ai_response = asyncio.run(process_message(example_input))
            if ai_response:
                st.rerun()
        
        if st.button("➕ Math Query"):
            example_input = "What is 123 + 456?"
            st.session_state.conversation_history.append(HumanMessage(content=example_input))
            ai_response = asyncio.run(process_message(example_input))
            if ai_response:
                st.rerun()
        
        if st.button("💰 Mortgage Query"):
            example_input = "Calculate monthly payment for $300,000 loan at 3.5% for 30 years"
            st.session_state.conversation_history.append(HumanMessage(content=example_input))
            ai_response = asyncio.run(process_message(example_input))
            if ai_response:
                st.rerun()
        
        st.markdown("---")
        st.subheader("💡 Tips")
        st.markdown("""
        - Ask about weather in any city
        - Perform mathematical calculations
        - Calculate mortgage payments
        - Have natural conversations
        - Use the examples above to get started
        """)

if __name__ == "__main__":
    main()