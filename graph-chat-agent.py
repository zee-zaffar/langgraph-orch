
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
    workflow.add_node("agent",call_model)
    workflow.add_node("tools", tool_node)

    workflow.add_edge(START,"agent")
    workflow.add_conditional_edges("agent",should_continue)
    workflow.add_edge("tools","agent")

    return workflow.compile()

#Main execution
graph = get_graph()
response = graph.invoke({"messages": [HumanMessage(content="Add 5 and 8?")]})

response_content = response["messages"][-1].content
print("Final Response:", response_content)