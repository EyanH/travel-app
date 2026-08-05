# Travel App — Multi-Trip Planner

## What this is

A multi-trip planning and reference web app. Evolves the existing single-country Peru app (github.com/eyanh/peru-trip) into a country-agnostic system that supports any number of trips from one deployed instance.

**Users:** Eyan (owner) and small friend groups sharing a trip. Everyone with the link can view and edit; changes sync live via Firestore.

**Cost target:** $0 ongoing. Everything must fit within Firebase Firestore free tier (1 GB storage, 50K reads/day, 20K writes/day), GitHub Pages (free), and other free-forever services. No paid APIs.

## Preserved from the Peru app

The Peru app works great. Preserve its architecture and features. Do not introduce a build system.

- **Single-file React app** loaded from CDN (React 18.2 UMD). One `index.html`.
- **Firebase Firestore** for shared state sync (existing project `travel-app-277ca`).
- **localStorage** for offline fallback.
- **Open-Meteo** for weather (no key required).
- **DM Sans + Playfair Display** from Google Fonts.
- **Dark theme** with `#0d1117` background, quest-log aesthetic.
- **All 5 tabs on the detail view:** itinerary, flights, packing, quests, info.
- **All existing features:** editable fields, mini calendar, weather cards, quest log, hotel-distance calc, city flag detection, sync badge.

## What's new / different

### 1. Firebase collection structure

Currently: single doc at `trips/peru-trip-2026`.

New: `trips` is a collection. Each doc is one trip.

```
travel-app-277ca (existing Firebase project)
└── trips/ (collection)
    ├── peru-2026     (migrate existing Peru data here)
    ├── morocco-2026  (seed from trips/morocco-2026.json)
    └── ...
```

Each trip doc contains everything the current Peru doc contains (days, packing, checked, meta, flights, flnotes, quests) plus these new fields:

- `slug` (string, primary key, matches doc ID)
- `heroImage` (string URL for the tile and detail header)
- `country` (string, for tile display and flag lookup)
- `createdAt` (Firestore timestamp)
- `archived` (boolean, default false, for hiding old trips from tiles)

### 2. URL routing

The app is a single HTML file with two views selected by URL param:

- `/` or `/?` → **Homepage** with trip tiles
- `/?trip=morocco-2026` → **Detail view** for that trip (existing Peru UI)

If `?trip=slug` is present, load that trip's doc from Firestore. If missing or slug doesn't resolve to a doc, show the homepage.

Update `window.history.pushState` on tile click, no page reload.

### 3. Homepage tile view

A grid of postcards, one per trip. Each tile:

- Hero image (full bleed background)
- Country flag emoji (top left)
- Trip name in Playfair Display (large)
- Date range subtitle in DM Sans
- Quick stats row (X days, X cities)
- Subtle gradient overlay for text legibility
- Hover state: slight lift and scale
- Click: navigates to `?trip=slug`

Layout:
- Desktop: 3 columns
- Tablet: 2 columns
- Mobile: 1 column

Plus one **"+ New Trip"** tile at the end, dashed border, plus icon, muted styling.

### 4. New Trip modal

Triggered from the "+ New Trip" tile. Modal with fields:

- **Trip name** (required, e.g. "Morocco")
- **Subtitle** (optional, e.g. "Toronto → Marrakech → Sahara")
- **Start date** (required)
- **End date** (required)
- **Country** (required, single field, drives flag)
- **Hero image URL** (required, user pastes any image URL)
- **Slug** (auto-generated from name + year, e.g. "morocco-2026", editable if user wants)

On save:
1. Create Firestore doc at `trips/{slug}` with the fields above plus empty defaults for `days: []`, `packing: {}`, `checked: {}`, `quests: []`, `flights: []`.
2. Redirect to `?trip={slug}`.

If a doc with that slug already exists, show error and prompt to edit slug.

### 5. Detail view changes

The existing Peru UI, but with these small additions:

- **Back to Trips** button in the top-left header (returns to homepage)
- **Hero image** displayed as a banner at the top of the detail view (using the doc's `heroImage`)
- **Country flag** in the header alongside trip name
- **Delete trip** option in a settings menu (with confirmation)
- **Archive trip** option (soft-hide from homepage)

Everything else stays the same. All existing edit-in-place, quest, packing, weather features carry over.

### 6. Deletion of hard-coded Peru data

Remove these from `index.html`:

- `DOC_ID = "peru-trip-2026"` → replaced with dynamic slug from URL
- `DEFAULT_META`, `DEFAULT_DAYS`, `DEFAULT_QUESTS` → replaced with empty defaults or seeded from trip doc
- `FLAGS` → keep as a global lookup table but expand it (or better, drive from `country` field)
- `HOTEL_COORDS`, `CITY_COORDS` → move into each trip's doc as `hotelCoords` and `cityCoords`

The point: no hardcoded trip-specific data in the app code. Everything trip-specific lives in the Firestore doc.

## File structure

```
/travel-app
├── index.html              (the whole app, single file)
├── trips/
│   ├── morocco-2026.json   (seed data for Morocco, from this thread)
│   └── peru-2026.json      (optional: seed for Peru migration)
├── README.md
└── CLAUDE.md               (this file)
```

## Firestore schema (per trip doc)

```json
{
  "slug": "morocco-2026",
  "country": "Morocco",
  "createdAt": "<Firestore timestamp>",
  "archived": false,
  "heroImage": "https://images.unsplash.com/...",
  "meta": {
    "tripName": "Morocco",
    "subtitle": "Toronto → Marrakech → Sahara → Essaouira → Home",
    "startDate": "2026-09-20",
    "endDate": "2026-09-30",
    "stats": [
      {"n": "11", "l": "days"},
      {"n": "3", "l": "cities"},
      {"n": "1", "l": "desert night"},
      {"n": "2", "l": "flights"}
    ]
  },
  "days": [ /* Day objects, same schema as Peru */ ],
  "flights": [ /* preserved from Peru schema */ ],
  "flnotes": "",
  "packing": {
    "clothing": ["Light layers", "Warm evening top", ...],
    "tech": [...],
    "docs": [...],
    "misc": [...]
  },
  "checked": { "Light layers": false, ... },
  "quests": [ /* Quest objects, same schema as Peru */ ],
  "hotelCoords": {
    "marrakech": {"lat": 31.6295, "lon": -7.9811, "name": "Riad De Vinci"},
    "essaouira": {"lat": 31.5085, "lon": -9.7595, "name": "Essaouira Riad"}
  },
  "cityCoords": {
    "marrakech": {"lat": 31.6295, "lon": -7.9811},
    "essaouira": {"lat": 31.5085, "lon": -9.7595},
    "merzouga": {"lat": 31.0977, "lon": -4.0086}
  }
}
```

## Day types (existing TC config, preserve as-is)

- `travel` — transit days, dark blue accent
- `explore` — city days, green accent
- `trek` — adventure/desert days, orange accent
- `flex` — chill/work days, purple accent

Morocco data uses all four. If more types are needed in future trips, extend the `TC` object.

## Migration plan (deferred, do not do in v1)

Peru stays live at github.com/eyanh/peru-trip. Do not touch it. The new app is a fresh repo.

Later, if Eyan wants to consolidate: migration is a one-time script that reads the existing `trips/peru-trip-2026` Firestore doc, copies it to `trips/peru-2026`, and adds the new fields (`slug`, `country`, `heroImage`, `createdAt`, `archived`). This is out of scope for v1.

## Deployment

- GitHub Pages, deployed from `main` branch, root directory
- Repo must be public (private repos require paid GitHub plan for Pages)
- Custom domain optional (not needed for v1)

## Design guidelines

- Preserve the current dark aesthetic (`#0d1117` bg, `#e6edf3` text, `#21262d` cards)
- Preserve the `DM Sans` + `Playfair Display` font pairing
- Preserve the quest log aesthetic and category colors (adventure, cultural, food, activity)
- New homepage tiles should feel like postcards: hero image dominant, text overlaid in bottom-left, subtle gradient for legibility
- Homepage background: same `#0d1117` as detail view
- Homepage header: small logo/name at top, gentle. Not a big splash. This is a personal utility, not a landing page.

## What to build first (v1 scope)

In order:

1. **Refactor `index.html`** to remove hardcoded Peru data. Load trip data from Firestore based on URL param. If no `?trip=` param, render homepage.
2. **Homepage tile view** reading from `trips` collection.
3. **New Trip modal** with the fields listed above, creating a new Firestore doc.
4. **Detail view header additions** (back button, hero image banner, country flag).
5. **Seed Morocco data** into Firestore from `trips/morocco-2026.json` (a one-time seed script, or auto-seed on first load if doc doesn't exist).

## What to defer to v2

- Delete / archive UI
- Peru data migration
- Auto-fetch hero image from Wikimedia
- Trip templates ("copy structure from existing trip")
- Shared checklist state across users (currently everyone sees the same checked items, which is fine for friend groups)
- PWA / offline manifest
- Cost tracker per trip

## Working with Eyan

- Eyan is the Director of Content and Marketing at Lucky VR, comfortable with code and AI tools but not a full-time dev. Explain non-obvious choices.
- Ships pragmatically. Prefers "working and deployed" over "perfect."
- No em dashes in any user-facing copy (his rule). Use commas, colons, or parentheses.
- Small, iterative changes. Push often. Verify each change is live before moving on.
