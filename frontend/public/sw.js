const CACHE = 'lipi-v1';
const SHELL = ['/', '/dashboard', '/index.html'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// Network-first for API calls, cache-first for static assets
self.addEventListener('fetch', e => {
  const { request } = e;
  const url = new URL(request.url);

  // Always skip non-GET and API/WS calls — never cache clinical data
  if (request.method !== 'GET' || url.pathname.startsWith('/api') || url.pathname.startsWith('/ws')) return;

  e.respondWith(
    fetch(request)
      .then(res => {
        if (res.ok && res.type !== 'opaque') {
          const clone = res.clone();
          caches.open(CACHE).then(c => c.put(request, clone));
        }
        return res;
      })
      .catch(() => caches.match(request))
  );
});
