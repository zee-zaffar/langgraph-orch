
import asyncio
import os
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import AzureChatOpenAI
from langgraph.graph import StateGraph, START, END, MessagesState
from langchain_mcp_adapters.client import MultiServerMCPClient
import json
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

@tool
def calculate_monthly_mortgage(principal: float, interest_rate: float, years: int) -> dict:
    """
    Calculate the monthly mortgage payment and totals.

    Args:
        principal (float): Loan principal amount.
        interest_rate (float): Annual interest rate in percent (e.g. 3.5).
        years (int): Loan term in years.

    Returns:
        dict: {
            "monthly_payment": float,
            "total_payment": float,
            "total_interest": float,
            "monthly_rate": float,
            "num_payments": int
        }
    """
    if principal <= 0 or years <= 0:
        raise ValueError("principal and years must be positive")

    num_payments = int(years * 12)
    monthly_rate = (interest_rate / 100.0) / 12.0

    if monthly_rate == 0:
        monthly_payment = principal / num_payments
    else:
        monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)

    total_payment = monthly_payment * num_payments
    total_interest = total_payment - principal

    return {
        "monthly_payment": round(monthly_payment, 2),
        "total_payment": round(total_payment, 2),
        "total_interest": round(total_interest, 2),
        "monthly_rate": monthly_rate,
        "num_payments": num_payments,
    }

# Function to create and return an Azure OpenAI LLM instance
def get_azure_openai_llm():
    llm = AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),  # Changed to match .env file
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        temperature=0.7,
        max_tokens=1000
    )

    return llm

async def get_mcp_tools():

    # Load MCP configuration from JSON file (mcp_config.json expected next to this script)
    try:
        config_path = Path(__file__).parent / "mcp_config.json"

        with config_path.open("r", encoding="utf-8") as f:
            mcp_config = json.load(f)
    except Exception as e:
        print(f"⚠️ Failed to load MCP config from {config_path}: {e}")
        
    client = MultiServerMCPClient(mcp_config)

    # Get all tools from MCP math server
    tools = await client.get_tools()
    for tool in tools:
        print(f"🧪 MCP Tool: {tool.name} - {tool.description}")
    return tools

async def create_graph():
    mcp_tools = await get_mcp_tools()
    all_tools = [calculate_monthly_mortgage] + mcp_tools
    llm = get_azure_openai_llm()
    model = llm.bind_tools(all_tools)  

    async def call_model(state: MessagesState):
        messages = state["messages"]
        response = model.invoke(messages)
        return {"messages": [response]}  # Fixed: response is a single message, wrap in list

    def should_continue(state: MessagesState) -> bool:
        last_message = state["messages"][-1]
        if last_message.tool_calls:
            return "tools"
        return END

    tool_node = ToolNode(all_tools)
    workflow = StateGraph(MessagesState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue)
    workflow.add_edge("tools", "agent")

    # Add memory to maintain conversation history
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)

async def chat_loop():
    """Interactive chat loop with conversation memory"""
    graph = await create_graph()
    
    print("🤖 LangGraph Chat Agent")
    print("=" * 50)
    print("💬 Start chatting! (Type 'quit', 'exit', or 'q' to stop)")
    print("🔧 Available tools: Weather lookup, Math (addition)")
    print("=" * 50)
    
    # Thread ID for maintaining conversation memory
    thread_id = "chat-session-1"
    config = {"configurable": {"thread_id": thread_id}}
    
    # Initialize conversation history
    conversation_history = []
    
    while True:
        try:
            # Get user input
            user_input = input("\n💭 Human: ").strip()
            
            # Check for exit commands
            if user_input.lower() in ['quit', 'exit', 'q', 'bye']:
                print("\n👋 Thanks for chatting! Goodbye!")
                break
            
            # Skip empty inputs
            if not user_input:
                print("Human, please enter a message.")
                continue
            
            # Add user message to history
            conversation_history.append(HumanMessage(content=user_input))
            
            print("🔄 Processing...")
            
            # Invoke the graph with conversation history
            response = await graph.ainvoke(
                {"messages": conversation_history}, 
                config=config
            )
            
            # Get the latest AI response
            ai_response = response["messages"][-1]
            
            # Add AI response to history
            conversation_history = response["messages"]
            
            # Display response
            print(f"🤖 Assistant: {ai_response.content}")
            
            # Show tool usage if any
            if hasattr(ai_response, 'tool_calls') and ai_response.tool_calls:
                print(f"🔧 Used tools: {[call['name'] for call in ai_response.tool_calls]}")
                
        except KeyboardInterrupt:
            print("\n\n⚠️ Chat interrupted by user.")
            print("👋 Thanks for chatting! Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            print("Please try again.")

# Main execution
async def main():
    """Main execution function"""
    await chat_loop()

if __name__ == "__main__":
    asyncio.run(main())