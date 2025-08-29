const CACHE_NAME = "keenroute-cache-v12";
const urlsToCache = [
  "/",
  "/static/manifest.json",
  "/static/css/style.css",
  "/static/fonts/conquera-bold.woff2",
  "/static/fonts/conquera-bold.woff",
  "/static/fonts/ibmplexsans-regular.woff2",
  "/static/fonts/ibmplexsans-regular.woff",
  "/static/fonts/heebocyrillic.woff2",
  "/static/img/icon-72.png",
  "/static/img/icon-192.png",
  "/static/img/icon-512.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache)));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.map(key => {
        if (key !== CACHE_NAME) return caches.delete(key);
      }))
    )
  );
});

self.addEventListener("fetch", (event) => {
  event.respondWith(caches.match(event.request).then(response => response || fetch(event.request)));
});
