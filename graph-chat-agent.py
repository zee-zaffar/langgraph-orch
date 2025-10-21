
import os
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import AzureChatOpenAI
from langgraph.graph import StateGraph, START, END, MessagesState

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

llm = get_azure_openai_llm()
tools = [get_weather, add_two_numbers]
model = llm.bind_tools(tools)  # Fixed: bind tools to the llm instance, not create new AzureChatOpenAI
tool_node = ToolNode(tools)

def call_model(state: MessagesState):
   messages = state["messages"]
   response = model.invoke(messages)
   return {"messages": [response]}  # Fixed: response is a single message, wrap in list

def should_continue(state: MessagesState) -> bool:
    last_message = state["messages"][-1]
    # print ("Last message:", last_message.tool_calls)
    if last_message.tool_calls:
        return "tools"
    return END

def get_graph():
    workflow = StateGraph(MessagesState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue)
    workflow.add_edge("tools", "agent")

    # Add memory to maintain conversation history
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)

def chat_loop():
    """Interactive chat loop with conversation memory"""
    graph = get_graph()
    
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
            response = graph.invoke(
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

def demo_single_interaction():
    """Demo function showing single interaction"""
    print("\n🧪 Demo: Single Interaction")
    print("-" * 30)
    
    graph = get_graph()
    config = {"configurable": {"thread_id": "demo-session"}}
    
    response = graph.invoke(
        {"messages": [HumanMessage(content="Add 5 and 8, then tell me the weather in Chicago")]}, 
        config=config
    )
    
    response_content = response["messages"][-1].content
    print("Final Response:", response_content)

# Main execution
if __name__ == "__main__":
    print("🚀 LangGraph Chat Agent Starting...")
    
    # Choose execution mode
    print("\nSelect mode:")
    print("1. Interactive chat loop")
    print("2. Single demo interaction")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        chat_loop()
    elif choice == "2":
        demo_single_interaction()
    else:
        print("Invalid choice. Starting interactive chat loop...")
        chat_loop()