# importing required libraries
import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast?"
API_KEY = os.getenv("api_key")

# checking for api_key
api_key_value = os.getenv("api_key")
if not api_key_value:
    try:
        import streamlit as st
        api_key_value = st.secrets.get("api_key")
    except Exception:
        pass

API_KEY = api_key_value
if not API_KEY:
    raise RuntimeError("API key not found. Check .env or Streamlit secrets.")

# making directory for saving information in json files
os.makedirs("data",exist_ok=True)

def getting_current_weather(city):
    # get co-ordinates by city name
    params = {"q": city.strip().lower(), "appid": API_KEY, "units": "metric"}
    # try - catch block
    try:
        response = requests.get(BASE_URL,params=params,timeout=10)

    except requests.RequestException as e:

        return None, f"Could not reach the weather service: {e}"
    
    if response.status_code == 404:
        return None, f"No city found matching '{city}'."
    
    if response.status_code == 401:
        return None, "Weather API rejected the key."
    
    if not response.ok:
        return None, f"Weather service error {response.status_code}."

    weather_info = response.json()

    #storing it in json file
    with open("data/current.json","w") as f:
        json.dump(weather_info,f,indent=2)

    return weather_info

def getting_forecast(city):
    # getting one day ahead info by using city name
    # getting city details like lat and lon cordinates
    info = getting_current_weather(city)

    # if error then,
    if isinstance(info, str):
        return info
    
    city_lon = info["coord"]["lon"]
    city_lat = info["coord"]["lat"]

    complete_url = f"{FORECAST_URL}lat={city_lat}&lon={city_lon}&units=metric&appid={API_KEY}"
    try:
        response = requests.get(complete_url,timeout=10)

    except requests.RequestException as e:
        return f"Could not reach the weather service: {e}"

    if response.status_code == 404:
            return f"No found matching {city_lat} and {city_lon}."
        
    if response.status_code == 401:
        return "Weather API rejected the key."
    
    if not response.ok:
        return f"Weather service error {response.status_code}."

    # getting info in json
    forecast_info = response.json()
    # saving the forecast into json file
    with open("data/forecast.json","w") as f:
        json.dump(forecast_info,f,indent=2)

    return forecast_info

if __name__ == "__main__":
    print(getting_forecast("London"))

