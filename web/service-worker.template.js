/* Under the Tree service worker. Caches ONLY the static app shell listed below.
   It never handles cross-origin requests, so Firebase sign-in, Firestore (families, members, wishes, Gift Ideas,
   reservations, invites, setup codes) and retailer images always go straight to the network and are never stored here. */
'use strict';
const BUILD = '__UTT_BUILD__';
const CACHE = 'utt-shell-' + BUILD;
const SHELL = __UTT_SHELL__;
const SHELL_PATHS = new Set(SHELL.map(u => new URL(u, self.registration.scope).pathname));
self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL.map(u => new Request(u, {cache: 'reload'})))));
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k.startsWith('utt-shell-') && k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener('message', event => { if(event.data && event.data.type === 'SKIP_WAITING') self.skipWaiting(); });
self.addEventListener('fetch', event => {
  const req = event.request;
  if(req.method !== 'GET') return;
  const url = new URL(req.url);
  if(url.origin !== self.location.origin) return;           // Firebase/Google APIs, retailer images: not touched
  if(req.mode === 'navigate'){
    event.respondWith(caches.open(CACHE).then(c => c.match('index.html')).then(r => r || fetch(req)));
    return;
  }
  if(!SHELL_PATHS.has(url.pathname)) return;                 // anything else same-origin: network only, never stored
  event.respondWith(caches.open(CACHE).then(c => c.match(req, {ignoreSearch: true})).then(r => r || fetch(req)));
});
