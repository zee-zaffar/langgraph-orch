import asyncio
import os
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# Load environment variables
load_dotenv()

async def create_weather_session():
    """Create a session connection to the weather server"""
    weather_url = "https://app-weather-fouumxxwmaqmu.azurewebsites.net/mcp"
    
    try:
        # Create connection
        stream_context = streamablehttp_client(weather_url)
        read_stream, write_stream, _ = await stream_context.__aenter__()
        
        # Create session
        session = ClientSession(read_stream, write_stream)
        await session.__aenter__()
        await session.initialize()
        
        return session, stream_context
        
    except Exception as e:
        print(f"❌ Failed to create weather session: {e}")
        return None, None

async def get_weather_with_session(session, location):
    """Get weather using an existing session"""
    try:
        # List tools to find the weather tool
        tools_result = await session.list_tools()
        tools = tools_result.tools
        
        if not tools:
            return "No tools available"
        
        # Find weather tool (usually the first one)
        weather_tool = tools[0]
        
        # Call the weather tool
        result = await session.call_tool(weather_tool.name, {
            "location": location
        })
        
        return result.content[0].text if result.content else "No weather data"
        
    except Exception as e:
        return f"Error getting weather: {e}"

async def simple_weather_session_example():
    """Simple example of using weather session"""
    
    print("🌤️ Creating weather session...")
    session, stream_context = await create_weather_session()
    
    if not session:
        print("❌ Failed to create session")
        return
    
    try:
        # Test multiple weather queries
        locations = ["New York", "London", "Tokyo"]
        
        for location in locations:
            print(f"\n🔄 Getting weather for {location}...")
            weather = await get_weather_with_session(session, location)
            print(f"✅ {location}: {weather}")
        
    finally:
        # Clean up session
        try:
            await session.__aexit__(None, None, None)
            await stream_context.__aexit__(None, None, None)
            print("\n✅ Session closed properly")
        except:
            pass

# Integration example for your existing code
async def integrate_with_existing():
    """Example of how to integrate session-based weather into your existing multiserver setup"""
    
    # You can use this alongside your MultiServerMCPClient
    print("🔄 Creating direct weather session (bypassing MultiServerMCPClient)...")
    
    session, stream_context = await create_weather_session()
    
    if session:
        # Get weather directly
        weather_ny = await get_weather_with_session(session, "New York")
        weather_chicago = await get_weather_with_session(session, "Chicago")
        
        print(f"New York weather: {weather_ny}")
        print(f"Chicago weather: {weather_chicago}")
        
        # Clean up
        await session.__aexit__(None, None, None)
        await stream_context.__aexit__(None, None, None)

if __name__ == "__main__":
    print("="*50)
    print("🌤️ SIMPLE WEATHER SESSION EXAMPLE")
    print("="*50)
    
    asyncio.run(simple_weather_session_example())
    
    print("\n" + "="*50)
    print("🔧 INTEGRATION EXAMPLE")
    print("="*50)
    
    asyncio.run(integrate_with_existing())