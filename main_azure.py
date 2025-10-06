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
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
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

# Structured output for message classification
class MessageClassifier(BaseModel):
    message_type: Literal["cardiologist", "dentist", "general"] = Field(
        ..., 
        description="Classify if the message is related to cardiology (heart issues), dentistry (teeth) or a general issue."
    )

class State(TypedDict):
    """State schema for the conversation graph."""
    messages: Annotated[list, add_messages]
    message_type: str|None
    topic: str
    audience: Literal["children", "teenagers", "adults", "seniors"]
    length: Literal["short", "medium", "long"]

def classify_message(state: State):
    last_message = state["messages"][-1]
    classifier_llm = llm.with_structured_output(MessageClassifier)

    result = classifier_llm.invoke([
        {
            "role": "system", 
            "content": """Classify the user's message into one of the following categories that is most approrpirate to handle the issue:
            - cardiologist, 
            - dentist,
            - general """
        },
        {
            "role": "user", 
            "content": last_message.content
        }
    ])

    return {"message_type": result.message_type}

def cardilogist_agent(state: State):
    last_message = state["messages"][-1]
    mesages = [
        {
            "role": "system", 
            "content": """
                            You are a cardilogist agent that deal with all heart related issues.."
                            should only respond to issues relates to heart problems. 
                        """
        },
        {
            "role": "user", 
            "content": last_message.content
        }
    ]

    reply = llm.invoke(mesages)
    return {"messages": [{"role": "assistant", "content": "Cardiologist Agent:" + reply.content}]}

def general_agent(state: State):
    last_message = state["messages"][-1]
    mesages = [
        {
            "role": "system", 
            "content": """
                            You are a general agent that deal with headache, fever and pain related issues.."
                            should only respond to issues relates to general problems. 
                        """
        },
        {
            "role": "user", 
            "content": last_message.content
        }
    ]

    reply = llm.invoke(mesages)
    return {"messages": [{"role": "assistant", "content":"General Agent:" + reply.content}]}

def dentist_agent(state: State):
    last_message = state["messages"][-1]
    mesages = [
        {
            "role": "system", 
            "content": """
                            You are a dentist agent that deal with all teeth related issues.."
                            should only respond to issues relates to teeth problems. 
                        """
        },
        {
            "role": "user", 
            "content": last_message.content
        }
    ]
   
    reply = llm.invoke(mesages)
    return {"messages": [{"role": "assistant", "content": "Dentist Agent:" + reply.content}]}

def router(state: State):
    message_type = state.get("message_type","general")

    if message_type == "cardiologist":
        return {"next":"cardiologist"}
    elif message_type == "dentist":
        return {"next":"dentist"}
    else:
        return {"next":"general"}


# Create the state graph
graph_builder = StateGraph(State)

#Build the graph flow
graph_builder.add_node("classifier", classify_message)
graph_builder.add_node("router", router)
graph_builder.add_node("cardiologist", cardilogist_agent)
graph_builder.add_node("dentist", dentist_agent)    
graph_builder.add_node("general", general_agent)

graph_builder.add_edge(START, "classifier")
graph_builder.add_edge("classifier", "router")

graph_builder.add_conditional_edges(
    "router",
    lambda state: state.get("next"),
    {
        "cardiologist": "cardiologist",
        "dentist": "dentist",
        "general": "general"
    }
)

graph_builder.add_edge("cardiologist", END)
graph_builder.add_edge("dentist", END)
graph_builder.add_edge("general", END)

# Compile the graph
graph = graph_builder.compile()


def run_chatbot():
    state = {"messages": [], "message_type": None}

    while True:
        user_input = input("Message: ")
        if user_input == "exit":
            print("Bye")
            break

        state["messages"] = state.get("messages", []) + [
            {"role": "user", "content": user_input}
        ]

        state = graph.invoke(state)

        if state.get("messages") and len(state["messages"]) > 0:
            last_message = state["messages"][-1]
            print(f"Assistant: {last_message.content}")


if __name__ == "__main__":
    run_chatbot()