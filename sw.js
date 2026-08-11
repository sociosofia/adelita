const VERSION = 'adelita-pwa-v1.2';
const SHELL = [
  './', './index.html', './manifest.webmanifest', './METADADOS_BANCOS.json', './builder_v1.js', './history_v11.js', './commentary_v12.js',
  './assets/logo_etec_bayeux.png', './assets/logo_bayeux.png', './assets/logo_cps.png',
  './assets/icon-192.png', './assets/icon-512.png', './assets/icon-maskable-512.png',
  'https://cdn.jsdelivr.net/npm/jspdf@4.2.1/dist/jspdf.umd.min.js',
  'https://cdn.jsdelivr.net/npm/docx@9.7.1/dist/index.iife.js'
];
self.addEventListener('install', event => {
  event.waitUntil(caches.open(VERSION).then(cache => Promise.allSettled(SHELL.map(u => cache.add(u)))).then(()=>self.skipWaiting()));
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k=>k!==VERSION).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));
});
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  const sameOrigin = url.origin === self.location.origin;

  if (event.request.mode === 'navigate') {
    event.respondWith((async () => {
      try {
        const response = await fetch(event.request);
        if (response.ok) {
          const cache = await caches.open(VERSION);
          cache.put('./index.html', response.clone());
        }
        return response;
      } catch (_) {
        return (await caches.match('./index.html')) || (await caches.match('./'));
      }
    })());
    return;
  }

  if (sameOrigin && url.pathname.includes('/banks/')) {
    event.respondWith(caches.open(VERSION).then(async cache => {
      const cached = await cache.match(event.request);
      if (cached) return cached;
      const response = await fetch(event.request);
      if (response.ok) cache.put(event.request, response.clone());
      return response;
    }));
    return;
  }

  event.respondWith(caches.match(event.request).then(cached => cached || fetch(event.request).then(response => {
    if ((sameOrigin || url.hostname === 'cdn.jsdelivr.net') && response.ok) {
      caches.open(VERSION).then(cache => cache.put(event.request, response.clone()));
    }
    return response;
  }).catch(()=>caches.match('./index.html'))));
});
