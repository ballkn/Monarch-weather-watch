# Monarch Weather Watch

A shareable Hickory, NC monarch-migration weather app.

## What it does
- Shows a 0–100 monarch lookout score from Open-Meteo forecast data.
- Scores warmth, sunshine, rain risk, northerly wind, and an inferred post-cold-front signal.
- A GitHub Action checks each day at ~11:05 AM EDT in September and October.
- If score >= 75, it publishes a push alert to the shared ntfy topic.

## Fastest setup from an iPhone
1. Create a free GitHub account if needed.
2. In Safari, go to github.com and create a new PUBLIC repository, e.g. `monarch-weather-watch`.
3. Upload every file/folder from this project. Keep `.github/workflows/monarch.yml` in that exact path.
4. In the repo: Settings → Pages → Build and deployment → Source: **Deploy from a branch** → Branch `main`, folder `/ (root)` → Save.
5. After GitHub publishes it, open the GitHub Pages URL in Safari.
6. Tap Share → Add to Home Screen. The web app now launches like an app.
7. Install the free **ntfy** iPhone app from the App Store.
8. In ntfy, subscribe to topic: `monarch-weather-hickory-8284`
9. Allow notifications.
10. In GitHub: Actions → Monarch weather check → Run workflow. If current score is below 75, the action will correctly send nothing.

## Guaranteed end-to-end push test
To force one test alert without changing weather:
1. Open `check_weather.py` on GitHub and tap the pencil.
2. Temporarily change `if score>=75:` to `if score>=0:`.
3. Commit the change.
4. Go to Actions → Monarch weather check → Run workflow.
5. You should receive the ntfy push.
6. Change the line back to `if score>=75:` and commit again.

## Sharing
Send friends:
- your GitHub Pages web-app link; and
- the ntfy topic name `monarch-weather-hickory-8284`.

Anyone who subscribes to that topic receives the same Hickory alerts.

## Important
The cold-front detection is an inference from temperature/dew-point changes and wind, not an official frontal-analysis product. Treat the score as a migration-lookout heuristic, not a guarantee that monarchs will be present.
