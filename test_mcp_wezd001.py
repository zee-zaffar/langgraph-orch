import asyncio
import requests
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def test_mcp_server():
    """Test direct connection to MCP server using basic MCP client"""
    server_url = "https://wezd001.azurewebsites.net/mcp"
    
    print(f"🔗 Testing connection to: {server_url}")
    
    # First, test if the server is reachable
    try:
        response = requests.get(server_url, timeout=10)
        print(f"✅ Server responded with status: {response.status_code}")
    except Exception as e:
        print(f"❌ Server not reachable: {e}")
        return
    
    # Test MCP connection
    try:
        async with streamablehttp_client(server_url) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                print("🔄 Initializing MCP session...")
                await session.initialize()
                
                print("📋 Listing available tools...")
                tools_result = await session.list_tools()
                tools = tools_result.tools
                
                print(f"✅ Found {len(tools)} tools:")
                for i, tool in enumerate(tools, 1):
                    print(f"  {i}. {tool.name}")
                    print(f"     Description: {tool.description}")
                    if hasattr(tool, 'inputSchema'):
                        schema = tool.inputSchema
                        if schema and 'properties' in schema:
                            print(f"     Parameters: {list(schema['properties'].keys())}")
                    print()
                
                # Test calling a tool if available
                if tools:
                    first_tool = tools[0]
                    print(f"🧪 Testing tool: {first_tool.name}")
                    
                    # Try to call the tool with minimal parameters
                    try:
                        # You'll need to adjust parameters based on the actual tool schema
                        result = await session.call_tool(first_tool.name, {})
                        print(f"✅ Tool result: {result}")
                    except Exception as e:
                        print(f"⚠️ Tool call failed (this might be expected if parameters are required): {e}")
                
    except Exception as e:
        print(f"❌ MCP connection failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_server())