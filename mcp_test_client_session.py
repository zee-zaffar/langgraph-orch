import asyncio
import os
from dotenv import load_dotenv

try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
except ImportError as e:
    raise ImportError(
        "The package 'langchain_mcp_adapters' is not installed or the import path is incorrect. "
        "Install it with: pip install langchain-mcp-adapters or verify the package name and path."
    ) from e

from langgraph.prebuilt import create_react_agent
from langchain_openai import AzureChatOpenAI
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# Load environment variables
load_dotenv()

async def create_weather_session():
    """Create a direct session to weather server"""
    weather_url = "https://app-weather-fouumxxwmaqmu.azurewebsites.net/mcp"
    
    try:
        print(f"🌤️ Creating direct session to {weather_url}")
        async with streamablehttp_client(weather_url) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                
                # Get tools
                tools_result = await session.list_tools()
                tools = tools_result.tools
                
                print(f"✅ Weather session created with {len(tools)} tools")
                for tool in tools:
                    print(f"  - {tool.name}: {tool.description}")
                
                return session, tools
                
    except Exception as e:
        print(f"❌ Weather session failed: {e}")
        return None, None

async def test_weather_session():
    """Test weather session directly"""
    weather_url = "https://app-weather-fouumxxwmaqmu.azurewebsites.net/mcp"
    
    try:
        async with streamablehttp_client(weather_url) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                
                tools_result = await session.list_tools()
                tools = tools_result.tools
                
                if tools:
                    weather_tool = tools[0]
                    print(f"🧪 Testing {weather_tool.name}...")
                    
                    # Test weather for different locations
                    locations = ["New York", "Chicago", "Miami"]
                    
                    for location in locations:
                        try:
                            result = await session.call_tool(weather_tool.name, {
                                "location": location
                            })
                            content = result.content[0].text if result.content else "No data"
                            print(f"✅ {location}: {content}")
                        except Exception as e:
                            print(f"❌ {location}: {e}")
                
    except Exception as e:
        print(f"❌ Weather session test failed: {e}")

async def main():
    # Create Azure OpenAI LLM
    llm = AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        api_version=os.getenv("api_version"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        temperature=0.7,
        max_tokens=1000,
    )
    
    # client = MultiServerMCPClient(
    #     {
    #         "weather": {
    #             # Make sure to update to the full absolute path to your math_server.py file
    #             "url": "https://app-weather-fouumxxwmaqmu.azurewebsites.net/mcp",
    #             "transport": "streamable_http",
    #         },
    #         "math": {
    #             # Make sure you start your weather server on port 8000
    #             "url": "https://app-math-zee.azurewebsites.net/mcp",
    #             "transport": "streamable_http",
    #         },
    #         "math2": {
    #             # Make sure you start your weather server on port 8000
    #             "url": "http://127.0.0.1:8000/mcp",
    #             "transport": "streamable_http",
    #         }
    #     }
    # )

    print("🚀 Testing MCP server connections using sessions...")
    
    # Test weather server using direct session
    print("\n" + "="*50)
    print("📡 TESTING WEATHER SERVER WITH SESSION")
    print("="*50)
    
    await test_weather_session()
    
    print("\n" + "="*50)
    print("📡 TESTING WITH MULTISERVER CLIENT")
    print("="*50)
    
    # Test weather server individually using MultiServerMCPClient
    try:
        weather_client = MultiServerMCPClient({
            "weather": {
                "url": "https://app-weather-fouumxxwmaqmu.azurewebsites.net/mcp",
                "transport": "streamable_http",
            }
        })
        weather_tools = await weather_client.get_tools()
        print(f"✅ Weather server tools via MultiServer: {[tool.name for tool in weather_tools]}")
        
        # Create agent and test
        if weather_tools:
            agent = create_react_agent(llm, weather_tools)
            response = await agent.ainvoke({"messages": "what is the weather in Chicago?"})
            messages = response.get("messages", [])
            print("🤖 Agent Response:", messages[-1].content)
            
    except Exception as e:
        print(f"❌ Weather server error: {e}")
        
    # Test math server individually
    try:
        math_client = MultiServerMCPClient({
            "math": {
                "url": "https://app-math-zee.azurewebsites.net/mcp",
                "transport": "streamable_http",
            }
        })
        math_tools = await math_client.get_tools()
        print(f"✅ Math server tools: {[tool.name for tool in math_tools]}")
    except Exception as e:
        print(f"❌ Math server error: {e}")
    
    # Extract the AI response content from the messages
    # math_messages = math_response.get("messages", [])
    # if math_messages:
    #     # Get the last message (which should be the AI response)
    #     last_message = math_messages[-1]
    #     if hasattr(last_message, 'content'):
    #         ai_response_content = last_message.content
    #         print("AI Response Content:", ai_response_content)
    #     else:
    #         print("No content found in the last message")
    # else:
    #     print("No messages found in response")
    
    # print("Weather response:", weather_response)

if __name__ == "__main__":
    asyncio.run(main())