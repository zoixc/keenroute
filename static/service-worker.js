const CACHE_NAME = "keenroute-cache-v5"; // версия кеша
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

// При установке SW — кэшируем все нужные файлы
self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_PATHS))
  );
  self.skipWaiting();
});

// При активации — удаляем старые кеши
self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.map(key => key !== CACHE_NAME ? caches.delete(key) : null)
      )
    )
  );
  self.clients.claim();
});

// При запросах — сначала ищем в кеше, если нет — идем в сеть
self.addEventListener("fetch", event => {
  event.respondWith(
    caches.match(event.request).then(cachedResponse => {
      if (cachedResponse) return cachedResponse;

      return fetch(event.request).then(networkResponse => {
        // Кэшируем новые файлы динамически, кроме посторонних доменов
        if (event.request.url.startsWith(self.origin)) {
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, networkResponse.clone()));
        }
        return networkResponse;
      }).catch(() => {
        // fallback для оффлайн (можно добавить оффлайн-страницу)
        return cachedResponse;
      });
    })
  );
});
