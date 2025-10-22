
import asyncio
import os
from dotenv import load_dotenv
from langchain_core.tools import tool, BaseTool
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import AzureChatOpenAI
from langgraph.graph import StateGraph, START, END, MessagesState
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession
from pydantic import Field, BaseModel
from langchain_mcp_adapters.client import MultiServerMCPClient
import json
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

@tool
def get_weather(location: str) -> str:
    """
    Get the current weather for a given location.

            Args:
            location (str): The location to get the weather for.
            returns: str: The current weather description.
    """
    weather_data = {
        "Chicago": "Sunny, 75°F",
        "New York": "Cloudy, 68°F",
        "San Francisco": "Foggy, 60°F",
        "Texas": "Hot, 90°F",
        "London": "Rainy, 55°F",
        "Tokyo": "Clear, 70°F"
    }
    return weather_data.get(location, "Location not found")

@tool()
def add_two_numbers(num1: int, num2: int) -> int:
    """
    Add two numbers integers and return the sum as an integer.

            Args:
            num1 (int): First number to add.
            num2 (int): Second number to add.
            returns: int: The sum of two numbers.
    """
    return num1 + num2

#Bind the tool to the model

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

class DynamicMCPTool(BaseTool):
    """Dynamic LangGraph tool that wraps MCP server tools"""
    
    name: str = Field(..., description="Name of the MCP tool")
    description: str = Field(..., description="Description of the MCP tool")
    server_url: str = Field(..., description="MCP server URL")
    tool_name: str = Field(..., description="Original MCP tool name")
  
async def get_mcp_tools():

    client = MultiServerMCPClient({
            "math": {
            "url": "https://app-math.azurewebsites.net/mcp",
            "transport": "streamable_http"
        }
        # "math": {
        #     "url": "https://app-weather-fouumxxwmaqmu.azurewebsites.net/mcp",
        #     "transport": "streamable_http"
        # }
    })

    # Get all tools from MCP math server
    tools = await client.get_tools()
    # for tool in tools:
    #     print(f"🧪 MCP Tool: {tool.name} - {tool.description}")
    return tools

    # math_url = "https://app-math.azurewebsites.net/mcp"
    # try:
    #     async with streamablehttp_client(math_url) as (read_stream, write_stream, _):    
    #         async with ClientSession(read_stream, write_stream) as session:
    #             await session.initialize()  

    #             # Get mcp tools
    #             tools_result = await session.list_tools()
    #             print ("session initialized for MCP tools")
    #             mcp_tools = tools_result.tools
    #             print(f"✅ MCP session created with {len(mcp_tools)} tools")

    #             lg_tools = []

    #             if mcp_tools:
    #                for tool in mcp_tools:
    #                     print(f"🧪 Converted MCP tool: {tool.name}")
    #                     lg_tool = DynamicMCPTool(
    #                         name=tool.name,
    #                         description=tool.description,
    #                         server_url=math_url,
    #                         tool_name =tool.name
    #                     )
    #                     print(f"🧪 Converted MCP tool: {tool.name}...")
    #                     lg_tools.append(lg_tool)
    #             print ("Converted MCP tools to LG tools:", lg_tools)
    #             return lg_tools
    # except Exception as e:
    #     print(f"❌ MCP tool loading failed: {e}")
    #     return []
    
# async def setup_tools():
#     llm = get_azure_openai_llm()
#     lg_tools = await get_mcp_tools()
#     # lg_tools = await load_mcp_tools(mcp_tools)
#     print ("Converted LG tools:", lg_tools)

#     static_tools = [get_weather]
#     all_tools = static_tools + lg_tools
#     return all_tools, llm

async def create_graph():
    #Bind tools to the llm
    # all_tools, llm = await setup_tools()
    mcp_tools = await get_mcp_tools()
    all_tools = mcp_tools
    llm = get_azure_openai_llm()
    model = llm.bind_tools(all_tools)  # Fixed: bind tools to the llm instance, not create new AzureChatOpenAI  

    async def call_model(state: MessagesState):
        messages = state["messages"]
        response = model.invoke(messages)
        return {"messages": [response]}  # Fixed: response is a single message, wrap in list

    def should_continue(state: MessagesState) -> bool:
        last_message = state["messages"][-1]
        # print ("Last message:", last_message.tool_calls)
        if last_message.tool_calls:
            return "tools"
        return END

    # def get_graph():
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

# async def chat_loop():
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

async def demo_single_interaction():
    """Demo function showing single interaction"""
    print("\n🧪 Demo: Single Interaction")
    print("-" * 30)
    
    graph = await create_graph()
    config = {"configurable": {"thread_id": "demo-session"}}
    
    response = await graph.ainvoke(
        {"messages": [HumanMessage(content="Calculate interest using 5 percent rate on my $200000 mortgage balance using the math tool only. Explian which tool did you use to provide the answer")]}, 
        config=config
    )
    
    response_content = response["messages"][-1].content
    print("Final Response:", response_content)

# Main execution
async def main():
    """Main execution function - FIXED: Made async"""
    # print("🚀 LangGraph Chat Agent with MCP Integration Starting...")
    
    # # Choose execution mode
    # print("\nSelect mode:")
    # print("1. Interactive chat loop")
    # print("2. Single demo interaction")
    
    # choice = input("Enter choice (1 or 2): ").strip()
    
    # if choice == "1":
    #     chat_loop()
    # elif choice == "2":
    await demo_single_interaction()
    # else:
    #     print("Invalid choice. Starting interactive chat loop...")
    #     chat_loop()

if __name__ == "__main__":
    asyncio.run(main())