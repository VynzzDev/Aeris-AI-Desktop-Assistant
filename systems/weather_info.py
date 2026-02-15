import webbrowser
from urllib.parse import quote_plus


def weather_action(
    parameters: dict,
    player=None,
    session_memory=None
) -> str:
    """
    Weather report action.

    Pure action layer.
    - Opens Google weather search
    - Returns text response
    - Does NOT speak
    - Does NOT touch UI
    """

    city = parameters.get("city")
    time_param = parameters.get("time")

    if not city or not isinstance(city, str):
        return "Sir, the city is missing for the weather report."

    city = city.strip()

    if not time_param or not isinstance(time_param, str):
        time_param = "today"
    else:
        time_param = time_param.strip()

    search_query = f"weather in {city} {time_param}"
    encoded_query = quote_plus(search_query)
    url = f"https://www.google.com/search?q={encoded_query}"

    try:
        webbrowser.open(url)
    except Exception:
        return "Sir, I couldn't open the browser for the weather report."

    message = f"Showing the weather for {city}, {time_param}, sir."

    if session_memory:
        try:
            session_memory.set_last_search(
                query=search_query,
                response=message
            )
        except Exception:
            pass

    return message
