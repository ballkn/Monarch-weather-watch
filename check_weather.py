import json
import urllib.request
import datetime
import math
import os

from zoneinfo import ZoneInfo


# ------------------------------------------------------------
# SETTINGS
# ------------------------------------------------------------

LAT = 35.7345
LON = -81.3445

TOPIC = os.getenv(
    "NTFY_TOPIC",
    "monarch-weather-hickory-8284"
)

TIMEZONE = ZoneInfo("America/New_York")


# ------------------------------------------------------------
# DOWNLOAD WEATHER DATA
# ------------------------------------------------------------

url = (
    f"https://api.open-meteo.com/v1/forecast"
    f"?latitude={LAT}"
    f"&longitude={LON}"
    "&hourly="
    "temperature_2m,"
    "dew_point_2m,"
    "precipitation_probability,"
    "cloud_cover,"
    "wind_speed_10m,"
    "wind_direction_10m"
    "&temperature_unit=fahrenheit"
    "&wind_speed_unit=mph"
    "&timezone=America%2FNew_York"
    "&past_days=2"
    "&forecast_days=2"
)

with urllib.request.urlopen(url) as r:
    h = json.load(r)["hourly"]


# ------------------------------------------------------------
# TIME SETUP
# ------------------------------------------------------------

now = datetime.datetime.now(TIMEZONE)

times = [
    datetime.datetime.fromisoformat(t).replace(tzinfo=TIMEZONE)
    for t in h["time"]
]


# ------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------

def avg(key, indices):
    if not indices:
        return 0
    return sum(h[key][i] for i in indices) / len(indices)


def circular_mean_degrees(values):
    """
    Correctly averages compass directions.

    Example:
    350° + 10° should average to 0°,
    not 180°.
    """

    if not values:
        return 0

    sin_sum = sum(
        math.sin(math.radians(v))
        for v in values
    )

    cos_sum = sum(
        math.cos(math.radians(v))
        for v in values
    )

    angle = math.degrees(
        math.atan2(sin_sum, cos_sum)
    )

    return angle % 360


def wind_direction_name(degrees):
    directions = [
        "N", "NNE", "NE", "ENE",
        "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW",
        "W", "WNW", "NW", "NNW"
    ]

    index = round(degrees / 22.5) % 16
    return directions[index]


# ------------------------------------------------------------
# AFTERNOON FORECAST
# 12 PM through 5 PM
# ------------------------------------------------------------

afternoon = [
    i
    for i, t in enumerate(times)
    if (
        t.date() == now.date()
        and 12 <= t.hour <= 17
    )
]

if not afternoon:
    print("No afternoon forecast available.")
    raise SystemExit()


temp = max(
    h["temperature_2m"][i]
    for i in afternoon
)

cloud = avg(
    "cloud_cover",
    afternoon
)

rain = max(
    h["precipitation_probability"][i]
    for i in afternoon
)

wind = avg(
    "wind_speed_10m",
    afternoon
)

wind_directions = [
    h["wind_direction_10m"][i]
    for i in afternoon
]

direction = circular_mean_degrees(
    wind_directions
)

direction_name = wind_direction_name(
    direction
)


# ------------------------------------------------------------
# LOOK FOR RECENT COLD-FRONT SIGNAL
#
# Compare current/recent conditions against
# conditions roughly one day earlier.
# ------------------------------------------------------------

recent = [
    i
    for i, t in enumerate(times)
    if (
        0
        <= (now - t).total_seconds() / 3600
        <= 6
    )
]

prior = [
    i
    for i, t in enumerate(times)
    if (
        18
        <= (now - t).total_seconds() / 3600
        <= 30
    )
]


recent_dew = avg(
    "dew_point_2m",
    recent
)

prior_dew = avg(
    "dew_point_2m",
    prior
)

recent_temp = avg(
    "temperature_2m",
    recent
)

prior_temp = avg(
    "temperature_2m",
    prior
)


dew_drop = prior_dew - recent_dew
temp_drop = prior_temp - recent_temp


# ------------------------------------------------------------
# POST-FRONT SCORE
#
# Dew-point drop is weighted more heavily because
# frontal passage often produces a clearer humidity
# change than temperature change.
# ------------------------------------------------------------

post_front_score = (
    dew_drop * 1.6
    + temp_drop * 0.5
)

post_front_score = max(
    0,
    min(
        25,
        post_front_score
    )
)


# ------------------------------------------------------------
# DETERMINE IF WIND IS FAVORABLY NORTHERLY
#
# Accept:
# N, NNE, NE, NNW, NW
#
# In degrees this is approximately:
# 292.5° through 360°
# OR
# 0° through 67.5°
# ------------------------------------------------------------

northerly = (
    direction >= 292.5
    or direction <= 67.5
)


# ------------------------------------------------------------
# HARD QUALIFICATION CRITERIA
# ------------------------------------------------------------

warm = temp >= 68

sunny = cloud <= 50

dry = rain <= 25

useful_wind = wind >= 5

post_front = post_front_score >= 10


qualifies = (
    warm
    and sunny
    and dry
    and useful_wind
    and northerly
    and post_front
)


# ------------------------------------------------------------
# MONARCH WEATHER SCORE
# Used for information only.
# It does NOT override the hard requirements above.
# ------------------------------------------------------------

score = 0


# Temperature
if temp >= 72:
    score += 20
elif temp >= 68:
    score += 16
elif temp >= 64:
    score += 8


# Sunshine / cloud cover
if cloud <= 25:
    score += 20
elif cloud <= 50:
    score += 15
elif cloud <= 70:
    score += 7


# Rain
if rain <= 10:
    score += 15
elif rain <= 25:
    score += 10
elif rain <= 40:
    score += 4


# Wind direction
if northerly:
    score += 20


# Wind strength
if wind >= 10:
    score += 10
elif wind >= 5:
    score += 7


# Post-front signal
score += post_front_score


score = round(
    min(
        100,
        score
    )
)


# ------------------------------------------------------------
# LOG CURRENT CONDITIONS
# ------------------------------------------------------------

print(
    f"Monarch score: {score}/100"
)

print(
    f"Temperature: {temp:.0f}°F"
)

print(
    f"Cloud cover: {cloud:.0f}%"
)

print(
    f"Rain probability: {rain:.0f}%"
)

print(
    f"Wind: {direction_name} "
    f"{wind:.0f} mph"
)

print(
    f"Dew-point drop: "
    f"{dew_drop:.1f}°F"
)

print(
    f"Temperature drop: "
    f"{temp_drop:.1f}°F"
)

print(
    f"Post-front score: "
    f"{post_front_score:.1f}/25"
)


# ------------------------------------------------------------
# SEND ALERT ONLY IF ALL CONDITIONS QUALIFY
# ------------------------------------------------------------

if qualifies:

    body = (
        f"Score {score}/100 • "
        f"{temp:.0f}°F • "
        f"{cloud:.0f}% clouds • "
        f"{rain:.0f}% rain risk • "
        f"{direction_name} {wind:.0f} mph. "
        f"Recent post-front conditions detected. "
        f"Best lookout: about 1–4 PM."
    )

    req = urllib.request.Request(
        f"https://ntfy.sh/{TOPIC}",
        data=body.encode(),
        method="POST",
        headers={
            "Title":
            "🦋 High monarch potential in Hickory",

            "Priority":
            "high"
        }
    )

    urllib.request.urlopen(req).read()

    print(
        "Alert sent:",
        body
    )

else:

    reasons = []

    if not warm:
        reasons.append(
            "too cool"
        )

    if not sunny:
        reasons.append(
            "too cloudy"
        )

    if not dry:
        reasons.append(
            "rain risk too high"
        )

    if not useful_wind:
        reasons.append(
            "wind too light"
        )

    if not northerly:
        reasons.append(
            "wind not northerly"
        )

    if not post_front:
        reasons.append(
            "weak post-front signal"
        )

    print(
        "No alert:",
        ", ".join(reasons)
    )
