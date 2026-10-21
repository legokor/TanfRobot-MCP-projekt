"""The agent loop.

The tools come from the MCP server in ../mcp-server, which this script starts in the background.

Usage: uv run python agent.py "drive forward 30 cm, then measure the distance"
"""

import asyncio
import json
import sys
from pathlib import Path



import openai

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from llm import make_ask


SYSTEM_PROMPT = (
    "You control a robot using the given tools. "
    "Use the tools step by step to reach the user's goal. "
    "When the goal is reached, answer with a short summary and call no more tools."
)

#used if nothing is typed.
DEFAULT_GOAL = "Drive forward 30 cm, turn left, then measure the distance in front of you."

# MCP server
SERVER = StdioServerParameters(
    command="uv",
    args=["run", "--directory", str(Path(__file__).parent.parent / "mcp-server"), "python", "server.py"],
)


def to_llm_schema(tool) -> dict:
    """Convert an MCP tool description into the format the LLM API expects

    Args:
        tool: one tool from the MCP server's tool list (has name, description, input_schema)

    Returns:
        The same tool as an OpenAI-style "function" dict, ready to send to the LLM
    """
    return {
        "type": "function",
        "function": {"name": tool.name, "description": tool.description or "", "parameters": tool.input_schema},
    }


async def run_tool(session: ClientSession, name: str, arguments: str) -> str:
    """Run one tool call on the MCP server

    Args:
        session: the open connection to the MCP server
        name: the tool the LLM wants to call, e.g. "forward".
        arguments: the arguments as JSON text from the LLM, e.g. '{"distance": 70}'.

    Returns:
        The tool's answer as text, or "error: ..." if the call failed.
    """

    try:
        result = await session.call_tool(name, json.loads(arguments or "{}"))
    except Exception as e:
        return f"error: {e}"
    text = "\n".join(c.text for c in result.content if c.type == "text")

    return f"error: {text}" if result.is_error else text


async def run(goal: str, ask, session: ClientSession, max_steps: int = 10) -> str:
    """The agent loop.

    Args:
        goal: user's goal
        ask: function that sends the conversation to the LLM and returns its reply
        session: the open connection to the MCP server, used to run the tools
        max_steps: safety limit on how many times the LLM is asked

    Returns:
        The LLM's final answer, or a "stopped: ..." message if max_steps was reached.
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": goal},
    ]

    for step in range(1, max_steps + 1):
        msg = ask(messages)
        messages.append(msg.model_dump(exclude_none=True))

        if not msg.tool_calls:  # no tool call means done according to llm
            return msg.content or ""


        for call in msg.tool_calls:

            print(f"[step {step}] {call.function.name}({call.function.arguments})")
            result = await run_tool(session, call.function.name, call.function.arguments)

            print(f"  -> {result}")

            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

    return f"stopped: no answer after {max_steps} steps"



async def start(goal: str) -> str:
    """Start the MCP server, get its tools, connect to the LLM and run the loop.
    The MCP server is shut down automatically when this returns.

    Args:
        goal: what the user wants, in plain words.

    Returns:
        The LLM's final answer (from run).
    """
    async with stdio_client(SERVER) as (read, write):

        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = [to_llm_schema(t) for t in (await session.list_tools()).tools]
            return await run(goal, make_ask(tools), session)


def main() -> None:
    """Entry point"""
    sys.stdout.reconfigure(line_buffering=True)  # keep our lines in order with the server's [robot] lines

    goal = " ".join(sys.argv[1:]) or DEFAULT_GOAL
    print(f"Goal: {goal}\n")

    try:
        answer = asyncio.run(start(goal))

    except* (openai.APITimeoutError, openai.APIStatusError) as group:  
        error = group
        while isinstance(error, BaseExceptionGroup):  # unwrap to the original error from the LLM
            error = error.exceptions[0]

        sys.exit(f"\nLLM request failed: {error}\n")

    print(f"\nAgent: {answer}")


if __name__ == "__main__":
    main()
