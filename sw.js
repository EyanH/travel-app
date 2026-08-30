/* Travel app service worker.
   Goal: the app opens and your trips are readable with no signal (desert camp,
   the drive out of Yellowknife, a plane). Trip data itself is served from
   localStorage / Firestore's own cache by the app; this worker makes sure the
   app *shell* and its CDN dependencies are available offline.

   Strategy:
     - HTML  : network-first, fall back to cache  (so deploys show up immediately)
     - assets: cache-first, revalidate in background (CDN libs, fonts, icons, images)
*/
const VERSION = "v3";
const SHELL = "travel-shell-" + VERSION;
const ASSETS = "travel-assets-" + VERSION;

// Everything the app needs to boot with no network.
const PRECACHE = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./icons/apple-touch-icon.png",
  "https://unpkg.com/react@18.2.0/umd/react.production.min.js",
  "https://unpkg.com/react-dom@18.2.0/umd/react-dom.production.min.js",
  "https://unpkg.com/@babel/standalone@7.23.10/babel.min.js",
  "https://www.gstatic.com/firebasejs/10.12.2/firebase-app-compat.js",
  "https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore-compat.js",
  "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth-compat.js"
];

self.addEventListener("install", (e) => {
  e.waitUntil((async () => {
    const cache = await caches.open(ASSETS);
    // Individually, so one failed CDN fetch cannot abort the whole install.
    await Promise.all(PRECACHE.map(async (url) => {
      // version-pinned URLs, so the browser's own cache is fine (and gentler on the CDNs)
      try { await cache.add(url); } catch (err) { /* one bad CDN fetch must not break install */ }
    }));
    self.skipWaiting();
  })());
});

self.addEventListener("activate", (e) => {
  e.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(k => k !== SHELL && k !== ASSETS).map(k => caches.delete(k)));
    await self.clients.claim();
  })());
});

const isHTML = (req) =>
  req.mode === "navigate" ||
  (req.headers.get("accept") || "").includes("text/html");

// Live data and auth must never be served from cache.
const isBypass = (url) =>
  /firestore\.googleapis\.com|identitytoolkit|googleapis\.com\/identitytoolkit|securetoken|api\.open-meteo\.com|archive-api\.open-meteo\.com|geocoding-api\.open-meteo\.com|open\.er-api\.com|mymemory\.translated\.net|accounts\.google\.com|firebaseapp\.com\/__\/auth/.test(url);

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = req.url;
  if (isBypass(url)) return;                 // straight to network
  if (url.startsWith("chrome-extension")) return;

  if (isHTML(req)) {
    // Network-first so a fresh deploy is picked up right away.
    e.respondWith((async () => {
      try {
        const fresh = await fetch(req);
        const cache = await caches.open(SHELL);
        cache.put(req, fresh.clone());
        return fresh;
      } catch (err) {
        const cached = await caches.match(req, { ignoreSearch: true });
        return cached || caches.match("./index.html", { ignoreSearch: true })
          || new Response("<h1>Offline</h1><p>Open this once while online first.</p>",
               { headers: { "Content-Type": "text/html" } });
      }
    })());
    return;
  }

  // Assets: cache-first, refresh in the background.
  e.respondWith((async () => {
    const cached = await caches.match(req);
    const network = fetch(req).then(async (res) => {
      if (res && (res.ok || res.type === "opaque")) {
        const cache = await caches.open(ASSETS);
        cache.put(req, res.clone());
      }
      return res;
    }).catch(() => null);
    return cached || (await network) || new Response("", { status: 504 });
  })());
});
