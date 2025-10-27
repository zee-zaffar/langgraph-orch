# LangGraph Chat Agent with MCP Integration

A sophisticated chat agent built with LangGraph that integrates with Model Context Protocol (MCP) servers to provide weather information, mathematical calculations, and mortgage calculations through both console and web interfaces.

## 🚀 Features

- **Multiple Interfaces**: Choose between console-based or web-based (Streamlit) UI
- **MCP Integration**: Connects to MCP servers for weather and math operations
- **Built-in Tools**: Mortgage payment calculator
- **Conversation Memory**: Maintains chat history throughout sessions
- **Real-time Processing**: Async processing for responsive interactions

## 🛠️ Available Tools

### MCP Server Tools
- **Weather Lookup**: Get current weather for any location
- **Math Operations**: Addition, subtraction, multiplication, division

### Built-in Tools  
- **Mortgage Calculator**: Calculate monthly payments, total interest, and payment schedules

## 🎯 Usage Options

### Option 1: Quick Launcher (Recommended)
```bash
python launcher.py
```
Choose between console (1) or web UI (2) from the interactive menu.

### Option 2: Direct Console Mode
```bash
python graph-chat-agent.py
```

### Option 3: Direct Web UI Mode  
```bash
streamlit run streamlit_app.py
```
Then open http://localhost:8501 in your browser.

## 📋 Requirements

Install dependencies:
```bash
pip install -r requirements.txt
```

## 🔧 Configuration

1. **Environment Variables**: Copy `.env.example` to `.env` and configure:
   - Azure OpenAI credentials
   - API endpoints and keys

2. **MCP Configuration**: `mcp_config.json` contains MCP server settings

## 🖥️ Interface Comparison

| Feature | Console UI | Streamlit Web UI |
|---------|------------|------------------|
| **Ease of Use** | Terminal commands | Point-and-click web interface |
| **Visualization** | Text-only | Rich formatting, buttons, sidebar |
| **Tool Feedback** | Basic text | Visual indicators and status |
| **Examples** | Manual typing | Pre-built example buttons |
| **Session Management** | Single session | Persistent web session |
| **Deployment** | Local only | Can be deployed to web |

## 💡 Example Queries

- "What's the weather in Paris?"
- "Calculate 150 + 275"  
- "What is 15% of 2000?"
- "Calculate mortgage payment for $400,000 loan at 4.2% for 30 years"
- "What's 25 multiplied by 16?"

## 🔍 Project Structure

```
├── graph-chat-agent.py     # Core LangGraph implementation  
├── streamlit_app.py        # Streamlit web UI
├── launcher.py             # Interface launcher script
├── mcp_config.json         # MCP server configuration
├── requirements.txt        # Python dependencies
└── README.md              # This file
```