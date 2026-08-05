# Travel

A multi-trip planning app. One deployed page, unlimited trips, live sync across devices and travel companions.

## Live

After deploy: `https://<your-username>.github.io/<repo-name>/`

- Homepage: `/`
- A trip: `/?trip=morocco-2026`

## Features

- Postcard homepage grouped into Upcoming and Past, with countdowns
- Per-trip detail: itinerary, flights, packing, quests, info
- Everything editable in place, saved automatically
- Live sync via Firebase Firestore (project `travel-app-277ca`), localStorage fallback
- Live weather per city via Open-Meteo (no key)
- Auto country flag + hero image when a trip does not specify one
- Handles both the new trip schema and the original Peru data shape

## Running locally

No build step. Double-click `index.html`, or serve the folder:

```bash
python -m http.server 8850
```

Then open `http://localhost:8850`.

## Deploying to GitHub Pages

1. Create a public repo on GitHub (e.g. `travel`)
2. From this folder:
   ```bash
   git remote add origin https://github.com/<you>/<repo>.git
   git branch -M main
   git push -u origin main
   ```
3. Repo Settings > Pages > Build and deployment > Deploy from a branch > `main` / root
4. Wait ~1 minute; your app is live.

## Notes on Firebase

The web config in `index.html` is safe to publish (Firebase web keys are public by
design; access is controlled by Firestore security rules). Because the app reads and
writes without sign-in, anyone with your Firestore rules open can edit trips. That is
the same setup the original Peru app used. If you want to lock it down later, we can
add a shared passphrase or Firebase Auth.

## Files

```
index.html               # The whole app
trips/morocco-2026.json  # Source copy of the Morocco seed (embedded in index.html)
_peru-reference.html     # Local backup of the original Peru app (gitignored)
CLAUDE.md                # Project spec
```
