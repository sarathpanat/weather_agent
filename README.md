# Weather MCP Server + Ollama Agent

A minimal test project:

- **`server.py`** – an MCP server exposing one tool, `get_weather(city)`, which fetches live weather from [Open-Meteo](https://open-meteo.com/) (free, **no API key**).
- **`agent.py`** – an agent that runs a local Llama model through Ollama, connects to the MCP server, and lets the model call the weather tool to answer questions.

```
You ──► agent.py ──► Ollama (llama3.2:3b)
            │              │  "call get_weather('Kozhikode')"
            ▼              ▼
        MCP client ──► server.py ──► Open-Meteo API
```

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com/download) installed and running
- Internet access (for the weather API)

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Pull a small model that supports tool calling
ollama pull llama3.2:3b
```

Make sure Ollama is running (`ollama serve`, or the desktop app is open).

## Run

**Interactive chat:**

```bash
python agent.py
```

```
You: What's the weather in Kozhikode right now?
  [tool call] get_weather({'city': 'Kozhikode'})
Agent: It's currently 28 °C in Kozhikode, Kerala with partly cloudy skies...
```

**One-shot:**

```bash
python agent.py "Is it raining in London?"
```

**Use a different model:**

```bash
OLLAMA_MODEL=llama3.1:8b python agent.py      # Windows (PowerShell): $env:OLLAMA_MODEL="llama3.1:8b"
```

> The model must support **tool calling**. Good small options: `llama3.2:3b` (default), `llama3.2:1b` (fastest, less reliable), `llama3.1:8b` (most reliable).

## Test the MCP server on its own

Before involving the agent, you can check the tool using the MCP Inspector:

```bash
mcp dev server.py
```

Open the URL it prints, go to **Tools → get_weather**, enter a city, and run it.

## Optional: use the same server in Claude Desktop

Add to `claude_desktop_config.json` (use absolute paths):

```json
{
  "mcpServers": {
    "weather": {
      "command": "/absolute/path/to/.venv/bin/python",
      "args": ["/absolute/path/to/weather-mcp-agent/server.py"]
    }
  }
}
```

Restart Claude Desktop afterwards.

## Project layout

```
weather-mcp-agent/
├── server.py          # MCP server + get_weather tool
├── agent.py           # Ollama agent (MCP client)
├── requirements.txt
└── README.md
```
