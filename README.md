# Outdoor Activity Planning Agent 🌦️

An LLM-powered agent that helps users plan outdoor activities by analyzing weather forecasts and recommending the most suitable time to go.

Built with **LangChain**, **Model Context Protocol (MCP)**, and the **Open-Meteo API**, this project demonstrates how an AI agent can dynamically discover external tools, retrieve real-world weather data, and make evidence-based recommendations instead of relying on general knowledge alone.

The agent evaluates hourly weather conditions to help users decide whether an outdoor activity is reasonable, which time window is preferable, or whether the activity should be avoided.

---

## Overview

Unlike a simple chatbot that provides generic weather advice, this agent follows a tool-based workflow to retrieve location-specific forecast data and reason over multiple weather factors.

Given a natural-language request, the agent:

1. Identifies the requested location and date.
2. Resolves the location into geographic coordinates.
3. Retrieves daily and hourly weather forecast data.
4. Analyzes weather conditions relevant to the activity.
5. Compares different time windows.
6. Provides a recommendation with an explanation based on the forecast.

The system is designed to avoid overly optimistic recommendations and to distinguish between the best available time window and a genuinely suitable time for an outdoor activity.

---

## Key Features

- **Natural Language Interaction** — Users can describe their outdoor plans using everyday language.
- **Dynamic Tool Discovery** — MCP tools are discovered at runtime rather than hard-coded into the agent.
- **Location Resolution** — Resolves city or place names into coordinates using geocoding.
- **Hourly Weather Analysis** — Evaluates hourly forecast data instead of relying only on daily summaries.
- **Time Window Comparison** — Compares morning, afternoon, and evening conditions to identify preferable time windows.
- **Weather-Aware Reasoning** — Considers precipitation probability, precipitation amount, temperature, feels-like temperature, wind, weather conditions, and daylight.
- **Safety-Oriented Recommendations** — Prioritizes thunderstorms and severe weather conditions over comfort-related factors.
- **Transparent Execution Trace** — Displays agent messages, tool calls, tool outputs, and the reasoning workflow available in the execution trace.

---

## Architecture

The project uses a LangChain agent connected to a local MCP server through the `stdio` transport.

```text
                 User Prompt
                     |
                     v
          +-----------------------+
          |   LangChain Agent    |
          |      Main.py         |
          +-----------------------+
                     |
                     v
          +-----------------------+
          |     MCP Client       |
          |  Tool Discovery      |
          +-----------------------+
                     |
           stdio communication
                     |
                     v
          +-----------------------+
          |    MCP Server        |
          |   mcp_server.py      |
          +-----------------------+
                     |
           +---------+----------+
           |                    |
           v                    v
 +------------------+  +----------------------+
 | geocode_location|  | get_weather_forecast |
 +------------------+  +----------------------+
           |                    |
           v                    v
 +------------------+  +----------------------+
 | Open-Meteo       |  | Open-Meteo          |
 | Geocoding API    |  | Forecast API        |
 +------------------+  +----------------------+
```

### Tool Workflow

The two tools have a dependency relationship:

`geocode_location` must be executed before `get_weather_forecast`, because the forecast tool requires the latitude and longitude returned by the geocoding step.

The agent discovers the tools through the MCP client and uses their returned results to construct subsequent tool calls.

---

## MCP Tools

The MCP server exposes exactly two tools:

| Tool | Description |
|---|---|
| `geocode_location(city)` | Resolves a city or place name into geographic coordinates. Returns matching locations with details such as country, administrative area, latitude, longitude, and timezone. |
| `get_weather_forecast(latitude, longitude, forecast_date)` | Retrieves daily and hourly forecast data for the specified coordinates and date. |

### 1. Geocoding

The `geocode_location` tool uses the Open-Meteo Geocoding API to search for a location.

It returns up to five matches, allowing the agent to distinguish between locations with similar names.

If the requested location is ambiguous, the agent should ask the user to clarify rather than assume the intended location.

### 2. Weather Forecast

The `get_weather_forecast` tool retrieves hourly and daily weather information for the selected location.

The hourly data includes:

- Temperature
- Apparent (feels-like) temperature
- Precipitation probability
- Precipitation amount (mm)
- Wind speed
- Weather codes and descriptions

The daily summary includes:

- Maximum and minimum temperature
- Maximum precipitation probability
- Maximum wind speed
- Sunrise and sunset times
- General weather conditions

Forecast requests are limited to today through the next 15 days.

---

## Weather Decision Framework

The agent is instructed to evaluate weather conditions through a structured decision framework rather than making recommendations based on a single metric.

| Factor | Why it matters |
|---|---|
| Precipitation probability | Estimates the likelihood of precipitation during a time period. |
| Precipitation amount | Indicates the expected quantity of precipitation; it is not interchangeable with probability. |
| Weather conditions | Identifies conditions such as rain, snow, fog, or thunderstorms. |
| Temperature | Evaluates the thermal conditions during the activity. |
| Feels-like temperature | Considers how the temperature may feel under actual conditions. |
| Wind speed | Helps assess comfort and potential difficulties for outdoor activities. |
| Sunrise & sunset | Ensures recommendations account for daylight availability. |
| Severe weather | Thunderstorms and severe conditions receive higher priority than comfort factors. |

### Recommendation Categories

The agent distinguishes between three types of conclusions:

- **Preferred time window:** The relatively best period compared with other available times.
- **Suitable time window:** A period that appears reasonably favorable based on the forecast.
- **Time window to avoid:** A period with unfavorable or potentially hazardous forecast conditions.

If no genuinely suitable time window exists, the agent should state that clearly instead of forcing a positive recommendation.

---

## Tech Stack

- **Python 3.11 / 3.12**
- **LangChain** — Agent creation and orchestration
- **LangGraph** — Agent execution framework
- **Model Context Protocol (MCP)** — Standardized tool integration
- **FastMCP** — MCP server implementation
- **LangChain MCP Adapters** — MCP client and tool integration
- **LangChain OpenAI** — LLM integration through OpenAI-compatible APIs
- **Open-Meteo** — Geocoding and weather forecast APIs
- **Requests** — HTTP API communication
- **Pydantic** — Data validation

---

## Project Structure

```text
Outdoor-Activity-Agent/
│
├── Main.py
│   └── Initializes the LLM, connects to the MCP server,
│       discovers tools, and runs the agent.
│
├── mcp_server.py
│   └── Defines and exposes weather-related MCP tools.
│
├── Tools.py
│   └── Handles geocoding, weather API requests,
│       data processing, and response formatting.
│
├── list model.py
│   └── Lists available models for the configured API provider.
│
├── requirements.txt
│   └── Project dependencies.
│
├── .env.example
│   └── Example environment configuration.
│
└── README.md
```

---

## Data Sources

The project uses the Open-Meteo APIs:

**Geocoding API**

https://geocoding-api.open-meteo.com/v1/search

Used to resolve location names into coordinates and identify possible matches.

**Forecast API**

https://api.open-meteo.com/v1/forecast

Used to retrieve hourly and daily weather forecasts.

No Open-Meteo API key is required for this example. An internet connection is required to access the APIs.

---

## Installation

### Prerequisites

- Python 3.11 or 3.12
- Git
- An LLM provider with an OpenAI-compatible API
- An API key for the chosen LLM provider
- Internet connection
- PowerShell (for the Windows commands below)

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/Outdoor-Activity-Agent.git
cd Outdoor-Activity-Agent
```

### 2. Create a virtual environment

```powershell
py -3.12 -m venv .venv
```

### 3. Activate the environment

```powershell
.venv\Scripts\Activate.ps1
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

### 4. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file in the project root directory using `.env.example` as a template.

Example configuration for Groq:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.groq.com/openai/v1
MODEL=openai/gpt-oss-20b
```

Choose a model that is currently available to your provider and supports tool calling.

> Never commit your `.env` file or expose your API key publicly.

---

## Usage

Start the agent by running:

```bash
python Main.py
```

Enter your outdoor activity request when prompted.

### Example

```text
Your prompt: I want to go hiking in Vienna tomorrow.
Is it a good idea? What time should I go?
```

The agent will:

1. Initialize the language model.
2. Connect to the local MCP server.
3. Discover available tools.
4. Resolve Vienna into coordinates.
5. Retrieve the weather forecast for tomorrow.
6. Analyze the hourly weather conditions.
7. Compare potential time windows.
8. Generate a recommendation.

---

## Example Prompts

### Hiking

```text
I want to go hiking in Vienna tomorrow.
Is it a good idea? What time should I go?
```

### Picnic Planning

```text
I'm planning a picnic in Paris tomorrow afternoon.
Check the weather and tell me whether I should go
or choose another time.
```

### Cycling

```text
Would cycling in Amsterdam this Saturday be reasonable?
I'm especially concerned about strong wind and rain.
Analyze the forecast and explain your recommendation.
```

### Comparing Time Windows

```text
Check the weather for a walk in Rome tomorrow.
Compare morning, afternoon, and evening, then
recommend the best time window.
```

### Ambiguous Location

```text
I want to hike near Springfield tomorrow.
Check the weather.
```

If multiple locations match, the agent should clarify which Springfield is intended before requesting the forecast.

### Forecast Limit

```text
Can I plan a picnic in Berlin in three weeks?
Check the weather forecast.
```

If the requested date is outside the available forecast range, the agent should explain the limitation instead of inventing weather data.

### General Question (No Tool Needed)

```text
What should I pack for a short day hike in mild weather?
```

The agent can answer general questions without invoking weather tools when a location-specific forecast is unnecessary.

---

## Execution Trace

The application prints an execution trace to the terminal, making the agent's tool-based workflow observable.

The trace includes:

- Initialization stages
- MCP connection status
- Discovered tool names
- Agent messages
- Tool calls
- Tool results
- Final agent response

This helps inspect whether the agent correctly follows the expected tool sequence and uses retrieved forecast data to support its recommendation.

---

## Reliability & Design Considerations

- **Sequential Tool Dependency:** Geocoding must happen before forecast retrieval.
- **Location Ambiguity:** Multiple matching locations should not be resolved through guessing.
- **Forecast Limitations:** Weather forecasts are limited to a 15-day horizon.
- **Hourly Reasoning:** Recommendations should be based on hourly conditions, not just daily summaries.
- **Probability vs. Amount:** Rain probability and precipitation amount are evaluated separately.
- **Severe Weather Priority:** Thunderstorms and severe weather should override otherwise favorable conditions.
- **Daylight Awareness:** A low-rain period before sunrise may not be appropriate for recreational activities.
- **No Forced Recommendations:** If conditions are unfavorable throughout the day, the agent should say so.
- **Execution Limits:** The agent uses a recursion limit and timeout to reduce the risk of excessive execution or hanging.

---

## Limitations

- Weather forecasts are inherently uncertain and can change.
- Forecast availability is limited to the next 15 days.
- The system does not evaluate terrain, trail difficulty, local trail closures, or equipment.
- Weather conditions alone cannot establish whether an outdoor activity is safe.
- Recommendations depend on the quality of the selected LLM and its ability to correctly use tools.
- This project is an educational prototype, not a professional or emergency weather-safety system.

Always recheck the forecast and consult official local weather alerts before heading outdoors.

---

## Learning Objectives

This project explores practical concepts in agentic AI:

- Building tool-calling agents with LangChain
- Understanding the Model Context Protocol (MCP)
- Separating agent orchestration from tool implementation
- Connecting LLMs to external APIs
- Dynamic tool discovery
- Multi-step tool dependency management
- Structured decision-making from real-world data
- Designing system prompts for constrained reasoning
- Improving reliability through validation, timeouts, and error handling

---

## Future Improvements

- Add activity-specific decision criteria for hiking, cycling, picnics, and running.
- Incorporate official weather warnings and severe-weather alerts.
- Add additional environmental factors such as UV index and air quality.
- Improve recommendations with user preferences and risk tolerance.
- Support multi-day activity planning.
- Add a web-based user interface.
- Improve structured output for clearer forecast comparisons.
- Add automated tests for tools, API responses, and agent workflows.

---

## Disclaimer

This project provides forecast-based suggestions for outdoor activity planning. It is not a safety guarantee, emergency service, or substitute for official weather warnings and local expertise.

---

*Built as a hands-on project exploring LLM agents, MCP, external tools, and weather-aware decision-making.*
