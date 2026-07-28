# importing required libraries
from langchain.chat_models import init_chat_model
from langchain_groq import ChatGroq
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_agent
from dotenv import load_dotenv
from datetime import date
from collections import defaultdict
import json
from weather import getting_current_weather,getting_forecast

load_dotenv() # loading dotenv variables

#defining prompt
prompt = """You are a friendly weather assistant. You help people \
understand the weather and decide what to do about it.

## Rules
1. Never state weather figures from memory. Always call a tool first. If a \
tool fails, say so plainly — do not guess or substitute typical values.
2. Pick the right tool for the timeframe. "Right now", "outside", "at the \
moment" → current. "Tomorrow", "this weekend", "Thursday", "next few days" \
→ forecast. If the question spans both ("is it getting warmer?"), call both.
3. Always name the city and the time period your answer covers, so the user \
can tell you looked up the right place. Many city names are ambiguous.
4. If the user does not say which city, ask. Do not assume one.

## Giving advice
When asked what to wear, whether to cycle, whether to carry an umbrella, or \
whether an outdoor plan will work, base it on the actual numbers you \
retrieved and say which numbers drove your answer. For example: rain \
probability above 50% means take waterproofs; wind above 10 m/s makes \
cycling hard work; a temperature range of more than 8 degrees across the day \
means layers.

Be concrete about the trade-off rather than just listing data. If conditions \
are borderline, say so and give the user something to decide on — the best \
window in the day, or what would change your recommendation.

## Style
Answer in a few sentences of plain prose. Use Celsius. Round temperatures to \
whole numbers. No tables or bullet lists unless the user asks to compare \
several days. Do not repeat the raw JSON back at the user.

You may answer general weather questions from knowledge (how fog forms, what \
humidity means) without calling any tool. Only weather *observations* require \
a tool call."""

# adding today's date
system_prompt = prompt+f"\n\nToday's date is {date.today().isoformat()}."

#initialize model
# using llama-3 model
llm_model = init_chat_model(
    model_provider="groq",
    model="llama-3.3-70b-versatile",
    temperature=0,
)

@tool
def get_current_weather(city): # fetches current weather details
    """Get the weather conditions happening RIGHT NOW in a city.

    Args:
        city: City name, e.g. "Liverpool" or "Kolkata".

    Returns current temperature in Celsius, conditions, humidity and wind
    speed in m/s. Use for questions about weather at this moment.
    """

    data = getting_current_weather(city)
    if isinstance(data,str):
        return data

    return json.dumps({
        "place": f"{data['name']}, {data['sys']['country']}",
        "when": "current conditions",
        "units": "celsius, m/s",
        "temp_c": round(data["main"]["temp"]),
        "feels_like_c": round(data["main"]["feels_like"]),
        "conditions": data["weather"][0]["description"],
        "humidity_pct": data["main"]["humidity"],
        "wind_ms": round(data["wind"]["speed"], 1),
    })

@tool
def get_weather_forecast(city): # fetches weather details of next 5 days.
    """Get the 5-day weather FORECAST for a city.

    Args:
        city: City name, e.g. "Liverpool" or "Kolkata".

    Returns forecast slots at 3-hour intervals covering the next 5 days,
    with temperature in Celsius, rain probability (pop, 0-1) and wind speed
    in m/s. Timestamps are UTC. Use for any question about future weather.
    """
    data = getting_forecast(city)
    if isinstance(data, str):
        return data

    days = defaultdict(list)
    for slot in data["list"]:
        days[slot["dt_txt"][:10]].append(slot)

    summary = []
    for day, slots in days.items():
        temps = [s["main"]["temp"] for s in slots]
        summary.append({
            "date": day,
            "temp_min_c": round(min(temps)),
            "temp_max_c": round(max(temps)),
            "rain_chance_pct": round(max(s.get("pop", 0) for s in slots) * 100),
            "max_wind_ms": round(max(s["wind"]["speed"] for s in slots), 1),
            "conditions": slots[len(slots) // 2]["weather"][0]["description"],
        })

    return json.dumps({
        "place": f"{data['city']['name']}, {data['city']['country']}",
        "when": "5-day forecast",
        "units": "celsius, m/s",
        "daily": summary,
    })

# creating an agen
weather_agent = create_agent(
    model=llm_model,
    tools=[get_current_weather,get_weather_forecast],
    system_prompt=system_prompt
)

# getting result
if __name__ == "__main__":
    result = weather_agent.invoke({"messages": [
        {"role": "user", "content": "Should I cycle in Liverpool tomorrow?"}
    ]})

    for m in result["messages"]:
        m.pretty_print()