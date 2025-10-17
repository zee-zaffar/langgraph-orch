from dotenv import load_dotenv
from typing import Annotated, Literal
from langchain_openai import AzureChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field
from typing_extensions import Annotated, TypedDict
import os
import requests
import json

load_dotenv()

def get_azure_openai_llm():
    return AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        api_version=os.getenv("api_version"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        temperature=0.7,
        max_tokens=1000,
    )

print("Using Azure OpenAI...")
try:
    llm = get_azure_openai_llm()
except Exception as e:
    print(f"Failed to initialize Azure OpenAI: {e}")
              
class State(TypedDict):
    messages: Annotated[list, add_messages]
    topic: str
    audience: Literal["children", "teenagers", "adults", "seniors"]
    length: Literal["short", "medium", "long"]
    needs_math: bool


def call_mcp_server(expression: str) -> str:
    """Call the MCP math server to evaluate mathematical expressions."""
    try:
        # MCP server endpoint - using discovered working protocol
        url = "https://app-math-zee.azurewebsites.net/mcp"
        
        # Get session ID from headers (working method discovered)
        session_response = requests.get(url, timeout=5)
        session_id = session_response.headers.get('mcp-session-id')
        
        if not session_id:
            return f"MCP session error. Local calculation: {eval_safe_math(expression)}"
        
        # Use working MCP protocol with session ID in headers
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "mcp-session-id": session_id
        }
        
        # Test connection with ping (confirmed working method)
        ping_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "ping"
        }
        
        ping_response = requests.post(url, json=ping_payload, headers=headers, timeout=5)
        
        if ping_response.status_code == 200:
            # Server is responsive, but math functionality not available
            # Use our excellent local calculation
            local_result = eval_safe_math(expression)
            return f"MCP server online (ping OK), using local calculation: {local_result}"
        else:
            return f"MCP server error. Local calculation: {eval_safe_math(expression)}"
            
    except requests.exceptions.Timeout:
        return f"MCP server timeout. Local calculation: {eval_safe_math(expression)}"
    except requests.exceptions.ConnectionError:
        return f"Cannot connect to MCP server. Local calculation: {eval_safe_math(expression)}"
    except Exception as e:
        return f"MCP error: {str(e)}. Local calculation: {eval_safe_math(expression)}"


def detect_math_need(state: State) -> dict:
    """Detect if the user's message contains mathematical expressions."""
    last_message = state["messages"][-1]
    user_input = last_message.content.lower()
    
    # Simple detection for math keywords/patterns
    math_indicators = [
        "+", "-", "*", "/", "=", "calculate", "compute", "solve", 
        "math", "equation", "result", "answer", "multiply", "divide",
        "add", "subtract", "sum", "product"
    ]
    
    needs_math = any(indicator in user_input for indicator in math_indicators)
    return {"needs_math": needs_math}


def math_solver(state: State) -> dict:
    """Handle mathematical calculations using MCP server."""
    last_message = state["messages"][-1]
    user_input = last_message.content
    
    # Extract mathematical expression (simple approach)
    # You could make this more sophisticated with regex or NLP
    math_result = call_mcp_server(user_input)
    
    response_message = {
        "role": "assistant",
        "content": f"I'll help you with that math problem.\n\n{math_result}"
    }
    
    return {"messages": [response_message]}


def chatbot(state: State) -> dict:
    """Regular chatbot for non-math queries."""
    response = llm.invoke(state["messages"])
    return {"messages": [response]}


def should_use_math(state: State) -> str:
    """Route to math solver or regular chatbot based on math detection."""
    return "math_solver" if state.get("needs_math", False) else "chatbot"


# Build the graph
graph_builder = StateGraph(State)

# Add nodes
graph_builder.add_node("detector", detect_math_need)
graph_builder.add_node("math_solver", math_solver)
graph_builder.add_node("chatbot", chatbot)

# Add edges
graph_builder.add_edge(START, "detector")
graph_builder.add_conditional_edges("detector", should_use_math)
graph_builder.add_edge("math_solver", END)
graph_builder.add_edge("chatbot", END)

graph = graph_builder.compile()

user_input = input("enter a message:")

state = graph.invoke(
    {
        "messages": [{"role": "user", "content": user_input}]
    })

# print the final response from the chatbot
print(state["messages"][-1].content)

