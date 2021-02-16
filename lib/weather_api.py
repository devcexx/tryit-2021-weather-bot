import requests
import typing
from urllib.parse import quote
import os
from json_serde import JsonSerde, Float, Integer, String, Nested, List, Anything


API_KEY_ENVIRON_NAME = "OPENWEATHERMAP_API_KEY"
_loaded_api_key = None


def _api_key() -> str:
    global _loaded_api_key

    if _loaded_api_key is None:
        _loaded_api_key = os.environ.get(API_KEY_ENVIRON_NAME)
        if _loaded_api_key is None:
            raise Exception("Open Weather Map API key is not set."
                            "Make sure you've set the environment variable" +
                            API_KEY_ENVIRON_NAME)

    return _loaded_api_key


class WeatherCode(JsonSerde):
    id = Integer()
    main = String()
    description = String()
    icon = String()


class MainWeather(JsonSerde):
    temp = Float()
    feels_like = Float()
    humidity = Float()


class Weather(JsonSerde):
    main = Nested(MainWeather)
    name = String()
    weather = List(Nested(WeatherCode))


def weather_request_from_place_name(city: str) -> typing.Optional[Weather]:
    resp = requests.get("https://api.openweathermap.org/data/2.5/weather?"
                        f"q={quote(city)}"
                        f"&appid={_api_key()}")

    # Place not found
    if resp.status_code == 404:
        return None

    resp.raise_for_status()
    result = resp.json()
    return Weather.from_json(result)


def weather_request_from_location(lat: float, lon: float) -> typing.Optional[Weather]:
    resp = requests.get("https://api.openweathermap.org/data/2.5/weather?"
                        f"lat={lat}&lon={lon}"
                        f"&appid={_api_key()}")

    # Place not found
    if resp.status_code == 404:
        return None

    resp.raise_for_status()
    result = resp.json()
    return Weather.from_json(result)


# The Weather Main codes for which we have a special image associated.
# Source: https://openweathermap.org/weather-conditions
KNOWN_MAIN_CODES = [
    "Thunderstorm",
    "Drizzle",
    "Rain",
    "Snow",
    "Clear",
    "Clouds"
]


def image_name_for_weather_code(code: WeatherCode) -> str:
    # Clouds group starts at 801, Code 800 is "Clear"
    if code.id > 800 and code.id < 803:
        # If weather is cloud, but no so much cloudy, use a different image.
        return "partial_clouds"
    elif code.main not in KNOWN_MAIN_CODES:
        # We don't have a specific image for this case. Just return a
        # generic image.
        return "oh-oh"
    else:
        return code.main.lower()
