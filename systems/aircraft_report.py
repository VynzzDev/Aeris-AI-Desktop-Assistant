import os
import math
import time
import requests
import webbrowser
import re
from difflib import SequenceMatcher

MY_LAT = float(os.getenv("LAT", 40.7908711))
MY_LON = float(os.getenv("LON", -73.3746079))

OPENSKY_STATES = "https://opensky-network.org/api/states/all"
OPENSKY_FLIGHTS = "https://opensky-network.org/api/flights/aircraft"


def _normalize(text: str):
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _smart_match(user_input: str, command: str):
    user = _normalize(str(user_input) if user_input else "")
    cmd = _normalize(str(command) if command else "")

    if cmd in user:
        return True

    user_words = set(user.split())
    cmd_words = set(cmd.split())

    if cmd_words and len(user_words & cmd_words) / len(cmd_words) >= 0.6:
        return True

    return SequenceMatcher(None, user, cmd).ratio() >= 0.6


def match_commands(user_input: str, commands):
    if not commands:
        return False
    if not isinstance(commands, (list, tuple)):
        commands = [commands]
    return any(_smart_match(user_input, cmd) for cmd in commands)


def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def get_nearby_aircraft(radius_km=200):
    lamin, lamax = MY_LAT - 1, MY_LAT + 1
    lomin, lomax = MY_LON - 1, MY_LON + 1

    try:
        r = requests.get(
            f"{OPENSKY_STATES}?lamin={lamin}&lamax={lamax}&lomin={lomin}&lomax={lomax}",
            timeout=10,
        )
        data = r.json()
    except Exception:
        return []

    aircraft = []

    for s in data.get("states", []) or []:
        lat, lon = s[6], s[5]
        if lat is None or lon is None:
            continue

        dist = haversine(MY_LAT, MY_LON, lat, lon)
        if dist > radius_km:
            continue

        aircraft.append({
            "icao24": s[0],
            "callsign": (s[1] or "Unknown").strip(),
            "country": s[2] or "Unknown",
            "distance": dist,
            "velocity": s[9] or 0,
            "heading": s[10] or 0,
        })

    return aircraft


def get_flight_route(icao24):
    now = int(time.time())
    begin = now - 6 * 3600
    try:
        r = requests.get(
            f"{OPENSKY_FLIGHTS}?icao24={icao24}&begin={begin}&end={now}",
            timeout=10
        )
        flights = r.json()
        if flights:
            f = flights[-1]
            return f.get("estDepartureAirport"), f.get("estArrivalAirport")
    except Exception:
        pass
    return None, None


def generate_aircraft_report():
    planes = get_nearby_aircraft()

    if not planes:
        return "Sir, no aircraft detected in your operational airspace."

    total = len(planes)
    closest = min(planes, key=lambda x: x["distance"])

    dist = closest["distance"]
    speed = closest["velocity"] * 3.6
    heading = closest["heading"]

    if dist < 50:
        situation = "approaching your position"
    elif dist < 120:
        situation = "passing through nearby airspace"
    else:
        situation = "operating at a safe distance"

    dep, arr = get_flight_route(closest["icao24"])
    dep = dep or "unknown origin"
    arr = arr or "unknown destination"

    return (
        f"Sir, radar scan complete. "
        f"I have detected {total} aircraft in your vicinity. "
        f"The nearest one is {closest['callsign']}, registered in {closest['country']}. "
        f"It is approximately {dist:.1f} kilometers away, "
        f"traveling at {speed:.0f} kilometers per hour, "
        f"heading {heading:.0f} degrees, "
        f"currently {situation}. "
        f"Estimated route is from {dep} to {arr}. "
        f"No immediate threat detected."
    )



def aircraft_action(parameters=None, player=None, session_memory=None):
    params = parameters or {}

    if params.get("open"):
        try:
            webbrowser.open(f"https://www.flightradar24.com/{MY_LAT},{MY_LON}/10")
        except Exception:
            pass
        return "Opening aircraft radar, sir."

    return generate_aircraft_report()


def handle_aircraft_command(user_text: str):
    txt = (user_text or "").strip().lower()

    detailed_cmds = [
        "give me aircraft details",
        "detailed aircraft report",
        "full detailed aircraft report",
    ]
    if match_commands(txt, detailed_cmds):
        return generate_aircraft_report()

    open_cmds = ["open aircraft", "open flight radar", "show aircraft map"]
    if match_commands(txt, open_cmds):
        try:
            webbrowser.open(f"https://www.flightradar24.com/{MY_LAT},{MY_LON}/10")
        except Exception:
            pass
        return "Opening aircraft radar, sir."

    summary_cmds = ["planes nearby", "how many aircraft", "how many planes"]
    if match_commands(txt, summary_cmds):
        planes = get_nearby_aircraft()
        return f"Sir, I currently detect {len(planes)} aircraft nearby."

    keywords = ["aircraft", "airplane", "plane", "flight", "air traffic"]
    if any(k in txt for k in keywords):
        planes = get_nearby_aircraft()
        return f"Sir, I currently detect {len(planes)} aircraft nearby."

    return None
