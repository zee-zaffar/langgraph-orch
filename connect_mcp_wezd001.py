import asyncio
import os
from dotenv import load_dotenv

try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
except ImportError as e:
    raise ImportError(
        "The package 'langchain_mcp_adapters' is not installed. "
        "Install it with: pip install langchain-mcp-adapters"
    ) from e

from langgraph.prebuilt import create_react_agent
from langchain_openai import AzureChatOpenAI

# Load environment variables
load_dotenv()

async def main():
    print("🚀 Connecting to MCP server at https://wezd001.azurewebsites.net/mcp")
    
    # Create Azure OpenAI LLM
    llm = AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        api_version=os.getenv("api_version"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        temperature=0.7,
        max_tokens=1000,
    )
    
    # Connect to the MCP server
    client = MultiServerMCPClient({
        "wezd001": {
            "url": "https://wezd001.azurewebsites.net/mcp",
            "transport": "streamable_http",
        }
    })
    
    try:
        # Get available tools from the server
        print("📋 Getting available tools...")
        tools = await client.get_tools()
        print(f"✅ Successfully connected! Found {len(tools)} tools:")
        
        for i, tool in enumerate(tools, 1):
            print(f"  {i}. {tool.name}")
            print(f"     Description: {tool.description}")
            if hasattr(tool, 'args_schema') and tool.args_schema:
                schema = tool.args_schema
                if hasattr(schema, 'schema'):
                    properties = schema.schema().get('properties', {})
                    if properties:
                        print(f"     Parameters: {list(properties.keys())}")
            print()
        
        # Create agent with the tools
        print("🤖 Creating LangGraph agent...")
        agent = create_react_agent(llm, tools)
        
        # Example prompts to test the MCP server
        test_prompts = [
            "What tools are available?",
            "Help me understand what this server can do",
        ]
        
        print("💬 Testing with example prompts...\n")
        
        for i, prompt in enumerate(test_prompts, 1):
            print(f"🔄 Test {i}: {prompt}")
            try:
                response = await agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})
                
                # Extract AI response
                messages = response.get("messages", [])
                if messages:
                    last_message = messages[-1]
                    if hasattr(last_message, 'content'):
                        print(f"🤖 Response: {last_message.content}")
                    else:
                        print("❌ No content in response")
                else:
                    print("❌ No messages in response")
                    
            except Exception as e:
                print(f"❌ Error with prompt '{prompt}': {e}")
            
            print("-" * 60)
        
        # Interactive mode
        print("\n🎯 Interactive Mode - Enter your prompts (type 'quit' to exit):")
        while True:
            try:
                user_input = input("\n💭 Your prompt: ").strip()
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not user_input:
                    continue
                
                print("🔄 Processing...")
                response = await agent.ainvoke({"messages": [{"role": "user", "content": user_input}]})
                
                # Extract and display response
                messages = response.get("messages", [])
                if messages:
                    last_message = messages[-1]
                    if hasattr(last_message, 'content'):
                        print(f"🤖 Response: {last_message.content}")
                    else:
                        print("❌ No content in response")
                else:
                    print("❌ No messages in response")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                
    except Exception as e:
        print(f"❌ Failed to connect to MCP server: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())