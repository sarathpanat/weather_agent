"""Ollama agent that talks to the weather MCP server.

Flow: start server.py over stdio -> list its tools -> give them to the Ollama
model -> when the model asks for a tool, run it through MCP -> feed the result
back -> print the final answer.

Usage:
    python agent.py                         # interactive chat
    python agent.py "weather in Kozhikode?" # one-shot
Env vars:
    OLLAMA_MODEL  (default: llama3.2:3b)
    OLLAMA_HOST   (default: http://localhost:11434)
"""

import asyncio
import os
import sys
from pathlib import Path

import ollama
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
SERVER_PATH = Path(__file__).parent / "server.py"

SYSTEM_PROMPT = (
    "You are a helpful weather assistant. When the user asks about the weather "
    "in any place, you MUST call the get_weather tool with the city name - never "
    "guess or use memorised data. After the tool returns, summarise the result "
    "briefly and clearly."
)


def mcp_tools_to_ollama(tools) -> list[dict]:
    """Convert MCP tool definitions into Ollama's tool format."""
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description or "",
                "parameters": t.inputSchema,
            },
        }
        for t in tools
    ]


async def ask(client, session, tools, messages, question: str) -> str:
    messages.append({"role": "user", "content": question})

    for _ in range(5):  # safety cap on tool-call rounds
        response = await client.chat(model=MODEL, messages=messages, tools=tools)
        msg = response.message
        messages.append(msg)

        if not msg.tool_calls:
            return msg.content or ""

        for call in msg.tool_calls:
            name, args = call.function.name, dict(call.function.arguments)
            print(f"  [tool call] {name}({args})", file=sys.stderr)
            result = await session.call_tool(name, args)
            text = "\n".join(c.text for c in result.content if c.type == "text")
            messages.append({"role": "tool", "tool_name": name, "content": text})

    return "Stopped: too many tool-call rounds."


async def main() -> None:
    server = StdioServerParameters(command=sys.executable, args=[str(SERVER_PATH)])
    client = ollama.AsyncClient(host=os.getenv("OLLAMA_HOST"))

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = mcp_tools_to_ollama((await session.list_tools()).tools)
            print(f"Model: {MODEL} | MCP tools: {[t['function']['name'] for t in tools]}")

            messages = [{"role": "system", "content": SYSTEM_PROMPT}]

            if len(sys.argv) > 1:  # one-shot mode
                print(await ask(client, session, tools, messages, " ".join(sys.argv[1:])))
                return

            print("Ask about the weather (type 'exit' to quit).")
            while True:
                try:
                    question = input("\nYou: ").strip()
                except (EOFError, KeyboardInterrupt):
                    break
                if question.lower() in {"exit", "quit", ""}:
                    break
                print("Agent:", await ask(client, session, tools, messages, question))


if __name__ == "__main__":
    asyncio.run(main())
