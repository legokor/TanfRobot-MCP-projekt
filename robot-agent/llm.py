"""Connection to the LLM
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


def make_ask(tools: list[dict]):
    """Set up the LLM connection once and return a function that asks the LLM.

    Args:
        tools: the tool descriptions sent with every request,
            so the LLM knows which tools it may call.

    Returns:
        ask(messages): sends the whole conversation to the LLM and returns its reply message
        (text, tool calls, or both).
    """

    load_dotenv(Path(__file__).parent / ".env")

    client = OpenAI(
        base_url=os.environ["LLM_BASE_URL"], 
        api_key=os.environ["LLM_API_KEY"],
        timeout=60,  
        max_retries=1,  # try once more on failure, then give up
    )

    model = os.environ["LLM_MODEL"]  

    def ask(messages: list[dict]):
        """Send the conversation to the LLM and return its reply

        Args:
            messages: the whole conversation so far (system, user, assistant and tool messages).
                The LLM has no memory, so everything is sent every time.

        Returns:
            The LLM's reply message: .content is its text, .tool_calls the tools it wants to call.
        """
        reply = client.chat.completions.create(model=model, messages=messages, tools=tools)
        return reply.choices[0].message 

    return ask
