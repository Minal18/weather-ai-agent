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

## Design notes

### Tool output shape matters more than prompt wording

The first working version passed the raw OpenWeather forecast response straight to the model: forty three hour slots, each with around twenty fields, roughly fifteen thousand characters of JSON per call.

It also contained a bug. The `units=metric` parameter was missing from the forecast request, so temperatures came back in Kelvin.

Asked whether to cycle in Liverpool tomorrow, the model read values around 294 and reported a high of 29C and a low of 22C. The real range was 17.5C to 25.1C.

It did not error. It did not notice the values were implausible. It produced confident, well written, wrong advice.

Two changes fixed it:

* The tools now aggregate the forty slots into six daily summaries and return only the fields that answer a weather question.
* Every tool response carries an explicit `"units": "celsius, m/s"` field, so a unit mismatch is visible to the model rather than silent.

Same model, same system prompt, same question. The difference was entirely in what the tools handed back.

### Errors are returned, not raised

The API client functions return a readable string on failure rather than raising. An exception propagating out of a tool ends the agent run; a returned message lets the model explain the problem to the user. A search for a place that does not exist produces "No city found matching ..." rather than a stack trace.

### Location is resolved once, up front

City names are ambiguous. Rather than letting the model guess or asking mid conversation, the app resolves the place before the chat opens and shows the user what OpenWeather actually matched. The resolved location is written into the system prompt, so follow up questions like "and Thursday?" work without repeating the city.

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

* Places are resolved by name and country code, so cities sharing a name within one country (Springfield in the United States, for example) may not resolve to the intended one. Passing coordinates through to the API instead of a name string would fix this.
* Forecast timestamps are UTC while the day boundaries used for aggregation are local, so daily summaries can be slightly off for locations far from UTC.
* Rain probability for a day is the maximum across that day's three hour slots, which reads high when there is a single wet window. A time weighted figure would be more representative.
* The hosted app sleeps after a period of inactivity and takes around thirty seconds to wake on the first visit.
