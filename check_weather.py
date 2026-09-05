import json, urllib.request

TOPIC = "monarch-weather-hickory-8284"

body = "🦋 Test successful. Monarch Weather Watch can send push notifications to this phone."

req = urllib.request.Request(
    f"https://ntfy.sh/{TOPIC}",
    data=body.encode(),
    method="POST",
    headers={
        "Title": "Monarch Weather Watch test",
        "Priority": "high"
    }
)

urllib.request.urlopen(req).read()
print("Test alert sent")
