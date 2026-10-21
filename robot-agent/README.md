# robot-agent

Give a goal in plain words, the LLM decides which robot tools to call, the loop passes those calls to the MCP server and sends the results back, until the goal is reached.

The tools live in [`../mcp-server`](../mcp-server/README.md). `agent.py` starts that server in the background by itself, so you only run `agent.py`.

Rn the tools are mocks, they print what the robot would do (and return fixed answers.

```
Goal: Drive forward 30 cm, turn left, then measure the distance in front of you.

[step 1] forward({"distance":30})
  [robot] forward 30.0 cm, speed 30
  -> ok: drove 30.0 cm
[step 2] turn({"angle":90})
  [robot] turn 90.0 degrees
  -> ok: turned 90.0 degrees
[step 3] get_distance({"angle":0})
  [robot] measure distance at 0.0 degrees
  -> 42 cm

Agent: I have successfully driven forward 30 cm, turned left 90 degrees, and measured the distance in front of the robot, which is 42 cm.
```

## Files

| File | What it does |
|---|---|
| `agent.py` | Starts the MCP server, gets its tool list, then loops: ask the LLM → pass its tool calls to the server → repeat. Max 10 steps. |
| `llm.py` | Connects to the LLM using the settings in `.env`. |
| `.env.example` | Settings template. Copy it to `.env` and add your own key. Never commit .env. |

## Setup

### 1. Install uv

`uv` installs Python (3.12) and the packages for you

- **Windows** (PowerShell): `winget install --id=astral-sh.uv -e`
- **Linux / macOS:** `curl -LsSf https://astral.sh/uv/install.sh | sh`

 Then, in this folder:

```bash
uv sync
```

### 2. Get a free Gemini API key

1. Go to <https://aistudio.google.com/apikey> and sign in with a Google account
3. Click **Create API key**
4. Copy the key.

The free tier needs no credit card. It has rate limits (requests per minute and per day), which are enough for testing. 

### 3. Put the key in `.env`

1. `copy .env.example .env`

2. Open `.env` and paste your key after `LLM_API_KEY=`.

**!!Never commit `.env`**!!

## Run

```bash
uv run python agent.py "drive forward 50 cm, then turn right and check the floor color"
```

Without a goal it uses a default one.
