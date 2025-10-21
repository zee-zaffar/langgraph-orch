"""
Simple Chat Loop Example for LangGraph
This demonstrates different patterns for creating interactive chat experiences.
"""

import os
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import AzureChatOpenAI
from langgraph.graph import StateGraph, START, END, MessagesState

# Load environment variables
load_dotenv()

@tool
def simple_calculator(expression: str) -> str:
    """Calculate simple math expressions like '2+3' or '10*5'"""
    try:
        # Safe evaluation for basic math
        result = eval(expression.replace('^', '**'))
        return f"{expression} = {result}"
    except:
        return f"Cannot calculate: {expression}"

@tool
def get_time() -> str:
    """Get the current time"""
    from datetime import datetime
    return f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

# Set up LLM and tools
def get_llm():
    return AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        temperature=0.7,
        max_tokens=1000
    )

# Simple stateless chat loop
def simple_chat_loop():
    """Basic chat loop without memory - each message is independent"""
    llm = get_llm()
    tools = [simple_calculator, get_time]
    model = llm.bind_tools(tools)
    
    print("🤖 Simple Chat (No Memory)")
    print("Type 'quit' to exit")
    print("-" * 30)
    
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ['quit', 'exit']:
            break
            
        try:
            response = model.invoke([HumanMessage(content=user_input)])
            print(f"Assistant: {response.content}")
            
            # Handle tool calls if any
            if response.tool_calls:
                print("🔧 Using tools...")
                tool_node = ToolNode(tools)
                tool_results = tool_node.invoke({"messages": [response]})
                
                # Get final response after tool usage
                final_response = model.invoke([
                    HumanMessage(content=user_input),
                    response,
                    *tool_results["messages"]
                ])
                print(f"Assistant (after tools): {final_response.content}")
                
        except Exception as e:
            print(f"Error: {e}")

# Chat loop with manual memory management
def chat_with_memory():
    """Chat loop that manually maintains conversation history"""
    llm = get_llm()
    tools = [simple_calculator, get_time]
    model = llm.bind_tools(tools)
    tool_node = ToolNode(tools)
    
    print("🤖 Chat with Memory")
    print("Type 'quit' to exit, 'clear' to clear history")
    print("-" * 40)
    
    conversation = []
    
    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() in ['quit', 'exit']:
            break
        elif user_input.lower() == 'clear':
            conversation = []
            print("🧹 Conversation history cleared!")
            continue
            
        # Add user message to conversation
        conversation.append(HumanMessage(content=user_input))
        
        try:
            # Get AI response
            response = model.invoke(conversation)
            conversation.append(response)
            
            print(f"Assistant: {response.content}")
            
            # Handle tool calls
            if response.tool_calls:
                print("🔧 Using tools...")
                tool_results = tool_node.invoke({"messages": conversation})
                conversation.extend(tool_results["messages"])
                
                # Get final response
                final_response = model.invoke(conversation)
                conversation.append(final_response)
                print(f"Assistant (final): {final_response.content}")
                
        except Exception as e:
            print(f"Error: {e}")
            # Remove last user message if there was an error
            if conversation and isinstance(conversation[-1], HumanMessage):
                conversation.pop()

# LangGraph-based chat loop (most robust)
def langgraph_chat():
    """Full LangGraph implementation with proper state management"""
    
    def call_model(state: MessagesState):
        llm = get_llm()
        tools = [simple_calculator, get_time]
        model = llm.bind_tools(tools)
        
        messages = state["messages"]
        response = model.invoke(messages)
        return {"messages": [response]}
    
    def should_continue(state: MessagesState):
        last_message = state["messages"][-1]
        if last_message.tool_calls:
            return "tools"
        return END
    
    # Build graph
    workflow = StateGraph(MessagesState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode([simple_calculator, get_time]))
    
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue)
    workflow.add_edge("tools", "agent")
    
    # Compile with memory
    memory = MemorySaver()
    graph = workflow.compile(checkpointer=memory)
    
    print("🤖 LangGraph Chat (Full State Management)")
    print("Type 'quit' to exit")
    print("-" * 45)
    
    config = {"configurable": {"thread_id": "chat-thread"}}
    messages = []
    
    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() in ['quit', 'exit']:
            break
            
        messages.append(HumanMessage(content=user_input))
        
        try:
            result = graph.invoke({"messages": messages}, config=config)
            ai_response = result["messages"][-1]
            
            print(f"Assistant: {ai_response.content}")
            
            # Update messages with full conversation
            messages = result["messages"]
            
        except Exception as e:
            print(f"Error: {e}")

def main():
    """Main menu to choose chat type"""
    print("🚀 Chat Loop Examples")
    print("=" * 30)
    print("1. Simple Chat (No Memory)")
    print("2. Chat with Manual Memory")
    print("3. LangGraph Chat (Recommended)")
    print("4. Exit")
    
    while True:
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == "1":
            simple_chat_loop()
        elif choice == "2":
            chat_with_memory()
        elif choice == "3":
            langgraph_chat()
        elif choice == "4":
            print("👋 Goodbye!")
            break
        else:
            print("Invalid choice. Please select 1-4.")

if __name__ == "__main__":
    main()