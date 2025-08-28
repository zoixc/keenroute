const CACHE_NAME = "keenroute-cache-v6"; // версия кеша
const STATIC_PATHS = [
  "/",
  "/static/manifest.json",
  "/static/css/style.css",
  "/static/fonts/conquera-bold.woff",
  "/static/fonts/IBMPlexSans-Regular.woff",
  "/static/img/icon-72.png",
  "/static/img/icon-192.png",
  "/static/img/icon-512.png",
  "/static/img/icon-512-maskable.png"
];

// Установка и кэширование ресурсов
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_PATHS))
  );
});

// Активация: удаляем старые кеши
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.map(key => {
          if (key !== CACHE_NAME) return caches.delete(key);
        })
      )
    )
  );
});

// Перехват fetch-запросов и отдача из кеша
self.addEventListener("fetch", (event) => {
  event.respondWith(
    caches.match(event.request).then(response => response || fetch(event.request))
  );
});
