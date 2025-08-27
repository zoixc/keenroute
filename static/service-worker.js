const CACHE_NAME = "keenroute-cache-v1";
const urlsToCache = ["/", "/static/manifest.json", "/static/css/style.css"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache)));
});

self.addEventListener("fetch", (event) => {
  event.respondWith(caches.match(event.request).then(response => response || fetch(event.request)));
});
