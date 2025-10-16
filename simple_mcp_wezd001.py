import asyncio
import os
from dotenv import load_dotenv

try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
except ImportError as e:
    raise ImportError(
        "Install with: pip install langchain-mcp-adapters"
    ) from e

from langgraph.prebuilt import create_react_agent
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import AIMessage

# Load environment variables
load_dotenv()

async def connect_and_prompt():
    """Simple function to connect to wezd001 MCP server and issue prompts"""
    
    # Azure OpenAI setup
    llm = AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        api_version=os.getenv("api_version"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        temperature=0.7,
        max_tokens=1000,
    )
    
    # Connect to your MCP server
    client = MultiServerMCPClient({
        "wezd001": {
            "url": "https://wezd001.azurewebsites.net/mcp",
            "transport": "streamable_http",
        }
    })
    
    try:
        # Get tools
        print("🔄 Connecting to https://wezd001.azurewebsites.net/mcp...")
        tools = await client.get_tools()
        print(f"✅ Connected! Found {len(tools)} tools:")
        
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
        
        # Create agent
        agent = create_react_agent(llm, tools)
        
        # Example prompts you can try
        prompts = [
            "What can you help me with?",
            "List all available tools",
            "What services are available on this server?",
        ]
        
        print(f"\n🤖 Testing with prompts...")
        
        for prompt in prompts:
            print(f"\n📝 Prompt: {prompt}")
            try:
                response = await agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})
                
                # Extract response
                messages = response.get("messages", [])
                if messages:
                    for message in messages:
                        if isinstance(message, AIMessage):
                            print(f"🤖 Response: {message.content}")
                            break
                else:
                    print("❌ No response received")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
        
        return client, agent
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None, None

async def send_custom_prompt(agent, prompt):
    """Send a custom prompt to the agent"""
    try:
        response = await agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})
        messages = response.get("messages", [])
        
        for message in messages:
            if isinstance(message, AIMessage):
                return message.content
        return "No response generated"
        
    except Exception as e:
        return f"Error: {e}"

# Example usage
async def main():
    # Connect to server
    client, agent = await connect_and_prompt()
    
    if agent:
        print("\n" + "="*50)
        print("🎯 Ready for custom prompts!")
        
        # Example of sending custom prompts
        custom_prompts = [
            "How do I use the available tools?",
            "Can you help me with a specific task?",
        ]
        
        for prompt in custom_prompts:
            print(f"\n📝 Custom prompt: {prompt}")
            response = await send_custom_prompt(agent, prompt)
            print(f"🤖 Response: {response}")

if __name__ == "__main__":
    asyncio.run(main())