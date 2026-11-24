
import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient


# ============================================================
# 1. PROJECT CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env", override=True)

required_env = [
    name
    for name in ("OPENAI_API_KEY", "MODEL")
    if not os.getenv(name)
]

if required_env:
    raise RuntimeError(
        "Missing environment variable(s): "
        + ", ".join(required_env)
        + ". Create a .env file from .env and fill it in."
    )

current_date = datetime.now().astimezone().date().isoformat()


# ============================================================
# 2. AGENT SYSTEM PROMPT
# ============================================================


SYSTEM_PROMPT = f"""

WEATHER ANALYSIS AND DECISION RULES:

1. Compare the requested time periods using hourly forecast data,
   not only the daily summary.

2. Evaluate these factors separately:
   - Precipitation probability
   - Precipitation amount (mm)
   - Weather conditions and weather codes
   - Temperature and feels-like temperature
   - Wind speed
   - Sunrise and sunset

3. Do not treat precipitation probability and precipitation
   amount as interchangeable metrics.

4. Give thunderstorms, lightning-related conditions, and
   severe weather warnings higher priority than comfort factors.
   Do not recommend outdoor activities during forecast
   thunderstorm conditions merely because precipitation
   probability is temporarily lower.

5. Distinguish between:
   - The best relative time window
   - A genuinely suitable time window
   - A time window that should be avoided

6. Never describe an entire period as dry or safe based on
   only one or two hourly values.

7. When recommending a time window, explicitly mention its
   start and end times and explain why it is preferable.

8. If no time window is genuinely suitable, clearly say so.
   Do not force a positive recommendation.

9. Consider daylight. A low-rain period before sunrise may
   not be suitable for a recreational walk.

10. Do not claim that weather conditions are safe. Provide
    a forecast-based recommendation with appropriate uncertainty.
"""



# ============================================================
# 3. RUN AGENT
# ============================================================

async def run_agent(question: str) -> None:

    print("\n[1] Initializing language model...", flush=True)

    model = ChatOpenAI(
        model=os.environ["MODEL"],
        base_url=(
            os.getenv("OPENAI_BASE_URL")
            or os.getenv("OPENAI_API_BASE")
        ),
        timeout=30,
        max_retries=1,
    )

    print("[2] Connecting to MCP server...", flush=True)

    # MCP server runs as a separate process over stdio.
    # sys.executable ensures the same Python environment is used.

    client = MultiServerMCPClient(
        {
            "weather": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [str(BASE_DIR / "mcp_server.py")],
            }
        }
    )

    # ========================================================
    # 4. MCP TOOL DISCOVERY
    # ========================================================

    print("[3] Discovering MCP tools...", flush=True)

    tools = await client.get_tools()

    discovered_tools = [tool.name for tool in tools]

    print(
        f"[4] Discovered MCP tools: {discovered_tools}",
        flush=True,
    )

    expected_tools = [
        "geocode_location",
        "get_weather_forecast",
    ]

    if sorted(discovered_tools) != sorted(expected_tools):
        raise RuntimeError(
            f"Unexpected MCP tool list: {discovered_tools}"
        )

    # ========================================================
    # 5. CREATE AGENT
    # ========================================================

    print("[5] Creating LangChain agent...", flush=True)

    agent = create_agent(
        model,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )

    # ========================================================
    # 6. EXECUTE AGENT
    # ========================================================

    print("\n[6] Starting agent execution...", flush=True)
    print(f"User question: {question}\n", flush=True)

    try:

        result = await asyncio.wait_for(
            agent.ainvoke(
                {
                    "messages": [
                        ("user", question)
                    ]
                },
                config={
                    "recursion_limit": 12
                },
            ),
            timeout=90,
        )

        print(
            "\n[7] Agent execution completed successfully.",
            flush=True,
        )

        # ====================================================
        # 7. PRINT AGENT TRACE
        # ====================================================

        print("\n" + "=" * 60)
        print("AGENT EXECUTION TRACE")
        print("=" * 60)

        for index, message in enumerate(result["messages"], start=1):

            print(f"\n--- Message {index} ---")
            message.pretty_print()

        print("\n" + "=" * 60)
        print("END OF AGENT TRACE")
        print("=" * 60)

    except asyncio.TimeoutError:

        print(
            "\n[ERROR] Agent execution exceeded 90 seconds.",
            flush=True,
        )

        print(
            "Check the model API, MCP server, and weather API.",
            flush=True,
        )

    except Exception as error:

        print(
            f"\n[ERROR] {type(error).__name__}: {error}",
            flush=True,
        )

        raise


# ============================================================
# 8. MAIN FUNCTION
# ============================================================

def main() -> None:

    print("=" * 55)
    print("OUTDOOR ACTIVITY PLANNING AGENT (MCP)")
    print("=" * 55)

    question = input("\nYour prompt: ").strip()

    if not question:
        print("Please enter a prompt.")
        return

    try:

        asyncio.run(run_agent(question))

    except KeyboardInterrupt:

        print("\nProgram interrupted by user.")

    except Exception as error:

        print(
            f"\n[FATAL ERROR] {type(error).__name__}: {error}"
        )


# ============================================================
# 9. ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
