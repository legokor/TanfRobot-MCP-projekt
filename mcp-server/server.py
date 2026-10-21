"""MCP server. It offers the robot's abilities as tools.


Usage: uv run python server.py    (normally started by an MCP client)
"""

import sys
import time
from typing import Annotated

from mcp.server.mcpserver import MCPServer
from pydantic import Field

mcp = MCPServer("tanfrobot")


def log(text: str) -> None:
    # stdout is reserved for MCP messages, so logs must go to stderr
    print(f"  [robot] {text}", file=sys.stderr)


# The docstrings and Field descriptions are what the LLM reads to decide what to call.

@mcp.tool()
def forward(
    distance: Annotated[float, Field(description="distance in cm, negative = backward")],
    speed: Annotated[float, Field(description="driving speed")] = 30,
) -> str:
    """Drive straight."""
    log(f"forward {distance} cm, speed {speed}")
    return f"ok: drove {distance} cm"


@mcp.tool()
def turn(
    angle: Annotated[float, Field(description="angle in degrees, positive = left (counter-clockwise), negative = right")],
) -> str:
    """Turn in place."""
    log(f"turn {angle} degrees")
    return f"ok: turned {angle} degrees"


@mcp.tool()
def get_distance(
    angle: Annotated[float, Field(description="sensor angle -90..90 degrees, 0 = straight ahead, positive = left")] = 0,
) -> str:
    """Measure the distance to the nearest obstacle with the distance sensor."""
    log(f"measure distance at {angle} degrees")
    return "42 cm"  # mock value


@mcp.tool()
def get_colors(
    duration: Annotated[float, Field(description="how far back to look, in seconds")] = 5,
) -> str:
    """Floor colors seen under the robot recently, oldest first."""
    log(f"colors of the last {duration} s")
    return "white, white, red"  # mock value


@mcp.tool()
def get_time() -> str:
    """Current time as a timestamp in seconds."""
    return f"{time.time():.1f}"


if __name__ == "__main__":
    mcp.run()
