from dotenv import load_dotenv
from typing import Annotated, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field
from typing_extensions import Annotated, TypedDict

load_dotenv()

llm = init_chat_model(
    "anthropic:claude-3-5-sonnet-latest"
    )

class State(TypedDict):
    message: Annotated[list, add_messages]
    topic: str
    audience: Literal["children", "teenagers", "adults", "seniors"]
    length: Literal["short", "medium", "long"]


graph_builder = StateGraph(State)

def chatbot(state: State):
    return {"message": [llm.invoke(state["message"])]}

graph_builder.add_node("chatbot", chatbot)

graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

graph = graph_builder.compile()

user_input = input("enter a message:")

state = graph.invoke(
    {
        "messages": [{"role": "user", "content": user_input}]
    })

# print the final response from the chatbot
print(state["messages"][-1]["content"])

