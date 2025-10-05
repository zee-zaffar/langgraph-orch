"""
Azure OpenAI integration with LangGraph example.
This demonstrates how to use Azure OpenAI API Key with LangGraph for building conversational AI.
"""

import os
from dotenv import load_dotenv
from typing import Annotated, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field
from typing_extensions import Annotated, TypedDict

# Try to import Azure OpenAI with fallback
try:
    from langchain_openai import AzureChatOpenAI
    AZURE_OPENAI_AVAILABLE = True
except ImportError:
    print("Warning: langchain-openai not installed. Azure OpenAI features will be disabled.")
    AZURE_OPENAI_AVAILABLE = False

# Load environment variables
load_dotenv()

def get_azure_openai_llm():
    """
    Initialize Azure OpenAI client with proper authentication.
    Uses API key authentication - for production, consider using Azure AD.
    """
    if not AZURE_OPENAI_AVAILABLE:
        raise ImportError("langchain-openai package not installed")
    
    return AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        temperature=0.7,
        max_tokens=1000,
    )

def get_fallback_llm():
    """Fallback to Anthropic if Azure OpenAI is not configured."""
    return init_chat_model("anthropic:claude-3-5-sonnet-latest")

# Initialize LLM based on available configuration
if AZURE_OPENAI_AVAILABLE and all([
    os.getenv("AZURE_OPENAI_API_KEY"),
    os.getenv("AZURE_OPENAI_ENDPOINT"),
    os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
]):
    print("Using Azure OpenAI...")
    try:
        llm = get_azure_openai_llm()
    except Exception as e:
        print(f"Failed to initialize Azure OpenAI: {e}")
        print("Falling back to Anthropic Claude...")
        llm = get_fallback_llm()
else:
    if not AZURE_OPENAI_AVAILABLE:
        print("Azure OpenAI package not available, using Anthropic Claude...")
    else:
        print("Azure OpenAI not configured, using Anthropic Claude...")
    llm = get_fallback_llm()

class State(TypedDict):
    """State schema for the conversation graph."""
    messages: Annotated[list, add_messages]
    topic: str
    audience: Literal["children", "teenagers", "adults", "seniors"]
    length: Literal["short", "medium", "long"]

# Create the state graph
graph_builder = StateGraph(State)

def chatbot(state: State):
    """
    Main chatbot function that processes messages using the configured LLM.
    Includes error handling for API failures.
    """
    try:
        response = llm.invoke(state["messages"])
        return {"messages": [response]}
    except Exception as e:
        print(f"Error calling LLM: {e}")
        # Return a fallback response
        fallback_response = {
            "role": "assistant", 
            "content": "I'm sorry, I'm having trouble processing your request right now. Please try again."
        }
        return {"messages": [fallback_response]}

# Build the graph
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

# Compile the graph
graph = graph_builder.compile()

def main():
    """Main execution function with proper error handling."""
    try:
        user_input = input("Enter a message: ")
        
        if not user_input.strip():
            print("Please enter a valid message.")
            return
        
        # Invoke the graph with user input
        state = graph.invoke({
            "messages": [{"role": "user", "content": user_input}],
            "topic": "general",
            "audience": "adults",
            "length": "medium"
        })
        
        # Print the final response from the chatbot
        if state["messages"]:
            print("\nBot response:")
            print(state["messages"][-1].content)
        else:
            print("No response received.")
            
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()