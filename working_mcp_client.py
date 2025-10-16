#!/usr/bin/env python3
"""
Working MCP Client using session ID from headers
"""

import requests
import json
import uuid
from typing import Optional, Dict, Any

class WorkingMCPClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session_id = None
        self.session = requests.Session()  # Use session to maintain cookies
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        
    def get_session_id(self) -> Optional[str]:
        """Get session ID from server headers"""
        
        try:
            # Make a simple request to get session ID
            response = self.session.get(f"{self.base_url}/mcp", headers=self.headers, timeout=5)
            
            # Extract session ID from headers
            session_id = response.headers.get('mcp-session-id')
            if session_id:
                self.session_id = session_id
                print(f"✅ Got session ID from headers: {session_id}")
                return session_id
            else:
                print("❌ No session ID in headers")
                return None
                
        except Exception as e:
            print(f"❌ Error getting session ID: {e}")
            return None
    
    def make_mcp_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make an MCP request with proper session handling"""
        
        if not self.session_id:
            if not self.get_session_id():
                return {"error": {"message": "Could not obtain session ID"}}
        
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": method,
            "sessionId": self.session_id  # Use the session ID from headers
        }
        
        if params:
            payload["params"] = params
            
        try:
            response = self.session.post(
                f"{self.base_url}/mcp", 
                json=payload, 
                headers=self.headers, 
                timeout=10
            )
            
            print(f"Request: {json.dumps(payload, indent=2)}")
            print(f"Response Status: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Response: {json.dumps(result, indent=2)}")
                return result
            else:
                error_text = response.text
                print(f"Error Response: {error_text}")
                return {"error": {"code": response.status_code, "message": error_text}}
                
        except Exception as e:
            return {"error": {"message": f"Request failed: {str(e)}"}}
    
    def list_tools(self) -> Dict[str, Any]:
        """List available tools"""
        return self.make_mcp_request("tools/list")
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool"""
        return self.make_mcp_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })
    
    def evaluate_math(self, expression: str) -> str:
        """Evaluate a mathematical expression using the MCP server"""
        
        # First try to list tools to see what's available
        tools_result = self.list_tools()
        
        if "result" in tools_result:
            print(f"✅ Available tools: {tools_result['result']}")
        
        # Try to call the math evaluation tool
        result = self.call_tool("evaluate_expression", {"expression": expression})
        
        if "result" in result:
            mcp_result = result["result"]
            
            # Extract the actual answer from the MCP response
            if isinstance(mcp_result, dict):
                if "content" in mcp_result:
                    content = mcp_result["content"]
                    if isinstance(content, list) and len(content) > 0:
                        return content[0].get("text", str(mcp_result))
                    else:
                        return str(content)
                else:
                    return str(mcp_result)
            else:
                return str(mcp_result)
                
        elif "error" in result:
            error = result["error"]
            return f"MCP Error: {error.get('message', str(error))}"
        else:
            return f"Unexpected response: {result}"

def test_working_mcp_client():
    """Test the working MCP client"""
    
    print("🚀 Testing Working MCP Client")
    print("=" * 50)
    
    client = WorkingMCPClient("https://app-math-zee.azurewebsites.net")
    
    # Test math evaluation
    expressions = ["2 + 3", "5 * 6", "10 / 2", "7 - 4"]
    
    for expression in expressions:
        print(f"\n🧮 Evaluating: {expression}")
        result = client.evaluate_math(expression)
        print(f"Result: {result}")

if __name__ == "__main__":
    test_working_mcp_client()