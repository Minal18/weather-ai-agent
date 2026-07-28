# LangChain Weather Agent

A conversational weather assistant built with LangChain tool calling. Ask it what the weather is doing, and it decides which tool to call, fetches real data from the OpenWeather API, and answers in plain language.

**Live app:** https://langchain-weather-agent-fhvczre2mvpjss9qq9fx6n.streamlit.app/

## What it does

You name a town or city, optionally with a country code, and the app confirms which place it resolved to before the conversation starts. From there you can ask about current conditions, the five day forecast, or practical questions such as whether to cycle tomorrow or whether to take a coat.

The assistant does not answer weather questions from memory. Every figure in its response comes from a tool call made during that turn, and the tool calls are visible in the interface under "What it looked up".

## Why this project

This was built to understand tool calling: how a language model is given functions it can invoke, how it decides which one fits a question, and what happens to its answers when the tool output is designed badly.

The interesting part turned out to be the last of those. Most of the debugging time went into the shape of what the tools return, not into prompting.

## How it works

An agent is a loop, not a single call:

1. The user message and system prompt go to the model, along with the schema of each available tool.
2. The model responds either with a final answer or with a request to call one or more tools.
3. If tools are requested, they run, and each result is appended to the message list as a tool message.
4. The full message list goes back to the model, which decides again.
5. This repeats until the model returns an answer with no further tool calls.

`create_agent` from LangChain implements this loop. The two tools are:

| Tool | Purpose | Returns |
|---|---|---|
| `get_current_weather` | Conditions right now | Temperature, feels like, conditions, humidity, wind |
| `get_weather_forecast` | Next five days | One summary row per day: min and max temperature, rain probability, max wind, typical conditions |

## Project structure

```
.
├── .streamlit/
│   └── config.toml    Theme
├── weather.py         OpenWeather API client
├── main.py            Tool definitions, system prompt, agent
├── app.py             Streamlit interface
└── requirements.txt
```

The separation is deliberate. `weather.py` is a faithful API client that returns what OpenWeather sends. `main.py` decides what a language model should actually see. Those are different concerns and they change for different reasons.

## Running locally

Requires Python 3.11 or later, a free OpenWeather API key, and a free Groq API key.

```bash
git clone https://github.com/YOUR_USERNAME/LangChain-Weather-Agent.git
cd LangChain-Weather-Agent
uv sync
```

Create a `.env` file in the project root:

```
api_key=your_openweather_key
GROQ_API_KEY=your_groq_key
```

Then:

```bash
uv run streamlit run app.py
```

## Built with

* **LangChain** for the agent loop and tool binding
* **Groq** running Llama 3.3 70B, chosen for a free tier with reliable native tool calling
* **OpenWeather** current weather and five day forecast endpoints
* **Streamlit** for the interface and hosting

## Known limitations

* The forecast times come back in UTC, but people think in their own local time. For places far from UTC, a daily summary can include a few hours from the day before or after.
* The chance of rain for a day is taken from the wettest three hour slot in that day. This makes the number look high even when only one short period is wet.
* The hosted app goes to sleep when nobody uses it. The first visit after that takes about thirty seconds to load.
