const CACHE_NAME = "keenroute-cache-v3"; // меняем версию, чтобы сбросить старый кеш
const urlsToCache = [
  "/", 
  "/static/manifest.json",
  "/static/css/style.css",
  "/static/fonts/conquera-bold.woff",
  "/static/fonts/IBMPlexSans-Regular.woff",
  "/static/img/icon-72.png",
  "/static/img/icon-192.png",
  "/static/img/icon-512.png"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.map(key => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      )
    )
  );
});

self.addEventListener("fetch", (event) => {
  event.respondWith(
    caches.match(event.request).then(response => response || fetch(event.request))
  );
});
