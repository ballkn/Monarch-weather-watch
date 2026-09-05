import json, urllib.request, datetime, os

LAT,LON=35.7345,-81.3445
TOPIC=os.getenv("NTFY_TOPIC","monarch-weather-hickory-8284")
url=(f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}"
     "&hourly=temperature_2m,dew_point_2m,precipitation_probability,cloud_cover,wind_speed_10m,wind_direction_10m"
     "&temperature_unit=fahrenheit&wind_speed_unit=mph&timezone=America%2FNew_York&past_days=2&forecast_days=2")
with urllib.request.urlopen(url) as r: h=json.load(r)["hourly"]

from zoneinfo import ZoneInfo
now=datetime.datetime.now(ZoneInfo("America/New_York"))
times=[datetime.datetime.fromisoformat(t).replace(tzinfo=ZoneInfo("America/New_York")) for t in h["time"]]
aft=[i for i,t in enumerate(times) if t.date()==now.date() and 12<=t.hour<=17]
if not aft: raise SystemExit()

avg=lambda key,inds: sum(h[key][i] for i in inds)/len(inds)
temp=max(h["temperature_2m"][i] for i in aft)
cloud=avg("cloud_cover",aft); rain=max(h["precipitation_probability"][i] for i in aft)
wind=avg("wind_speed_10m",aft); direction=avg("wind_direction_10m",aft)
recent=[i for i,t in enumerate(times) if 0 <= (now-t).total_seconds()/3600 <= 6]
prior=[i for i,t in enumerate(times) if 18 <= (now-t).total_seconds()/3600 <= 30]
dew_drop=avg("dew_point_2m",prior)-avg("dew_point_2m",recent)
temp_drop=avg("temperature_2m",prior)-avg("temperature_2m",recent)
post=max(0,min(25,dew_drop*1.6+temp_drop*.5))

x=abs(((direction+180)%360)-180)
north=20 if x<=22.5 else 16 if x<=67.5 else 9 if x<=90 else 0
score=(20 if temp>=72 else 16 if temp>=68 else 8 if temp>=64 else 0)
score+=(20 if cloud<=25 else 15 if cloud<=50 else 7 if cloud<=70 else 0)
score+=(15 if rain<=10 else 10 if rain<=25 else 4 if rain<=40 else 0)
score+=north+post
score=round(min(100,score))

# GitHub cache via repository variable would be better; simplest safe behavior is one scheduled run at 11:05 AM.
if score>=75:
    body=f"Score {score}/100 • {temp:.0f}°F • {cloud:.0f}% clouds • {rain:.0f}% rain risk • northerly score {north}/20. Best lookout: ~1–4 PM."
    req=urllib.request.Request(f"https://ntfy.sh/{TOPIC}",data=body.encode(),method="POST",
        headers={"Title":"🦋 High monarch potential in Hickory","Priority":"high","Tags":"butterfly"})
    urllib.request.urlopen(req).read()
    print("Alert sent:",body)
else:
    print("No alert. Score:",score)
