import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def connect_weather_server_with_session():
    """Connect to weather server using MCP ClientSession"""
    
    weather_server_url = "https://app-weather-fouumxxwmaqmu.azurewebsites.net/mcp"
    
    print(f"🌤️ Connecting to weather server: {weather_server_url}")
    
    try:
        # Create streamable HTTP client connection
        async with streamablehttp_client(weather_server_url) as (read_stream, write_stream, _):
            # Create MCP session
            async with ClientSession(read_stream, write_stream) as session:
                print("✅ Session established!")
                
                # Initialize the session
                print("🔄 Initializing session...")
                await session.initialize()
                print("✅ Session initialized!")
                
                # List available tools
                print("📋 Getting available tools...")
                tools_result = await session.list_tools()
                tools = tools_result.tools
                
                print(f"✅ Found {len(tools)} tools:")
                for i, tool in enumerate(tools, 1):
                    print(f"  {i}. {tool.name}")
                    print(f"     Description: {tool.description}")
                    if hasattr(tool, 'inputSchema') and tool.inputSchema:
                        schema = tool.inputSchema
                        if 'properties' in schema:
                            required = schema.get('required', [])
                            properties = schema['properties']
                            print(f"     Parameters:")
                            for param, details in properties.items():
                                req_marker = " (required)" if param in required else ""
                                param_type = details.get('type', 'unknown')
                                param_desc = details.get('description', 'No description')
                                print(f"       - {param} ({param_type}){req_marker}: {param_desc}")
                    print()
                
                # Test calling the weather tool if available
                if tools:
                    weather_tool = tools[0]  # Assuming first tool is weather
                    print(f"🧪 Testing tool: {weather_tool.name}")
                    
                    # Example: Get weather for New York
                    try:
                        if weather_tool.name == "get_weather":
                            result = await session.call_tool(weather_tool.name, {
                                "location": "New York, NY"
                            })
                            print(f"✅ Weather result: {result.content}")
                        else:
                            # Try calling with empty parameters to see what's required
                            result = await session.call_tool(weather_tool.name, {})
                            print(f"✅ Tool result: {result.content}")
                            
                    except Exception as tool_error:
                        print(f"⚠️ Tool call error: {tool_error}")
                        print("This might be normal if the tool requires specific parameters")
                
                # Test another location
                if tools and len(tools) > 0:
                    weather_tool = tools[0]
                    if weather_tool.name == "get_weather":
                        print(f"\n🌍 Testing weather for London...")
                        try:
                            result = await session.call_tool(weather_tool.name, {
                                "location": "London, UK"
                            })
                            print(f"✅ London weather: {result.content}")
                        except Exception as e:
                            print(f"❌ London weather error: {e}")
                
                return session, tools
                
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None

async def test_multiple_weather_queries():
    """Test multiple weather queries in one session"""
    
    weather_server_url = "https://app-weather-fouumxxwmaqmu.azurewebsites.net/mcp"
    
    locations = [
        "New York, NY",
        "London, UK", 
        "Tokyo, Japan",
        "Sydney, Australia",
        "Chicago, IL"
    ]
    
    print(f"🌍 Testing weather for multiple locations...")
    
    try:
        async with streamablehttp_client(weather_server_url) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                
                tools_result = await session.list_tools()
                tools = tools_result.tools
                
                if not tools:
                    print("❌ No tools available")
                    return
                
                weather_tool = tools[0]
                print(f"Using tool: {weather_tool.name}\n")
                
                for location in locations:
                    try:
                        print(f"🔄 Getting weather for {location}...")
                        result = await session.call_tool(weather_tool.name, {
                            "location": location
                        })
                        print(f"✅ {location}: {result.content}")
                        
                    except Exception as e:
                        print(f"❌ {location}: Error - {e}")
                    
                    print()  # Add spacing between results
                    
    except Exception as e:
        print(f"❌ Session error: {e}")

# Example usage
async def main():
    print("="*60)
    print("🌤️ WEATHER SERVER SESSION CONNECTION TEST")
    print("="*60)
    
    # Test 1: Basic connection and tool discovery
    print("\n1️⃣ Testing basic session connection...")
    session, tools = await connect_weather_server_with_session()
    
    if session and tools:
        print(f"✅ Successfully connected with {len(tools)} tools available")
    else:
        print("❌ Connection failed")
        return
    
    print("\n" + "="*60)
    
    # Test 2: Multiple weather queries
    print("\n2️⃣ Testing multiple weather queries...")
    await test_multiple_weather_queries()
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())