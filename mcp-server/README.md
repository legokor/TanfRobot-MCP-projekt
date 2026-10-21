# mcp-server

For now the tools are mocks, they log what the robot would do and return fixed answers.

## Tools

| Tool | Parameters | Returns (mock) |
|---|---|---|
| `forward` | `distance` (negative = backward movement), `speed` | `ok: drove 30.0 cm` |
| `turn` | `angle` (positive = left, negative = right) | `ok: turned 90.0 degrees` |
| `get_distance` | `angle`  (−90…90°, def. 0 = straight ahead) | `42 cm` |
| `get_colors` | `duration` (how far back to look, default 5) | `white, white, red` |
| `get_time` | - | current timestamp |


## Trying the tools by hand

Normally, the client (robot-agent) would launch the server.

The MCP Inspector is a web page where it is possible to only call the tools, to check they work.

Mini guide to make it work:

It needs [Node.js](https://nodejs.org/)

- **Windows:** `winget install OpenJS.NodeJS.LTS`
- **Fedora:** `sudo dnf install nodejs`
- **Ubuntu:** `sudo apt install nodejs npm`

Then, in this folder:

```bash
uv run mcp dev server.py
```

In the page that opens: Connect → Tools → List Tools, pick a tool, fill in the parameters, → Run Tool.

