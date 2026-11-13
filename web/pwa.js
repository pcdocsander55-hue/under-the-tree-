/* Under the Tree - web/PWA adapter. Loaded ONLY by the web build, before the shared app core.
   It adds: install help, the first-tap "Enter" step (browser audio rules), service-worker registration and
   the "update ready" prompt. It holds no family data, sends nothing anywhere, and has no analytics. */
(function(){
'use strict';
var BUILD = '__UTT_BUILD__';
var HINT_KEY = 'utt.web.installhint';   // 'never' or a timestamp: when the install tip may show again
function standalone(){
  try { return (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches) || window.navigator.standalone === true; }
  catch(e){ return false; }
}
var ua = navigator.userAgent || '';
var isIOS = /iPad|iPhone|iPod/.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
var root = document.documentElement;
root.classList.add('utt-web');
if(standalone()) root.classList.add('utt-standalone');
function lsGet(k){ try { return window.localStorage.getItem(k); } catch(e){ return null; } }
function lsSet(k, v){ try { window.localStorage.setItem(k, v); return true; } catch(e){ return false; } }
function el(tag, cls, html){ var e = document.createElement(tag); if(cls) e.className = cls; if(html != null) e.innerHTML = html; return e; }
function warn(msg){ try { console.warn('UTT web: ' + msg); } catch(e){} }

/* ---------- first deliberate tap: opening scene + music (only when music is on) ---------- */
function gate(musicOn, go){
  if(!musicOn){ go(); return; }
  var g = el('div', 'utt-gate');
  g.setAttribute('role', 'dialog'); g.setAttribute('aria-modal', 'true'); g.setAttribute('aria-label', 'Welcome');
  g.innerHTML = '<div class="utt-gate-card"><div class="utt-gate-title">Under the Tree</div>' +
    '<button type="button" class="utt-gate-btn">Enter Under the Tree</button>' +
    '<p class="utt-gate-note">Christmas music plays when you enter. You can turn it off in Settings.</p></div>';
  document.body.appendChild(g);
  var b = g.querySelector('button');
  b.addEventListener('click', function(){
    g.remove();
    try { go(); } catch(e){ warn('opening scene/music failed: ' + ((e && e.message) || e)); }
  }, {once: true});
  try { b.focus({preventScroll: true}); } catch(e){}
}

/* ---------- install help (Safari has no install button of its own) ---------- */
var deferredPrompt = null;
function hintAllowed(){
  if(standalone()) return false;
  var v = lsGet(HINT_KEY);
  if(v === 'never') return false;
  if(v && Number(v) > Date.now()) return false;
  return isIOS || !!deferredPrompt;
}
function showInstallPill(){
  if(document.querySelector('.utt-install') || !hintAllowed()) return;
  var p = el('button', 'utt-install', '\u2B07 Install Under the Tree');
  p.type = 'button';
  p.addEventListener('click', function(){
    if(deferredPrompt){ var d = deferredPrompt; deferredPrompt = null; d.prompt(); p.remove(); return; }
    openInstallHelp();
  });
  document.body.appendChild(p);
}
function openInstallHelp(){
  var joined = !!lsGet('utt.config');
  var o = el('div', 'utt-sheet-scrim');
  o.innerHTML = '<div class="utt-sheet" role="dialog" aria-modal="true" aria-labelledby="utt-ih-t">' +
    '<h2 id="utt-ih-t">Install Under the Tree</h2><ol>' +
    '<li>Tap the <b>Share</b> button <span aria-hidden="true">(the square with an arrow)</span>.</li>' +
    '<li>Tap <b>Add to Home Screen</b>. You may need to scroll down to find it.</li>' +
    '<li>Tap <b>Add</b>.</li></ol>' +
    '<p>Then open Under the Tree from your Home Screen. The installed app keeps its own sign-in, separate from Safari, ' +
    'so join your family inside the installed app.</p>' +
    (joined ? '<p><b>You have already joined in Safari.</b> In the installed app, join again with the same invite code and pick ' +
      'yourself from the list. That moves you over; it does not make a second you. Don\u2019t use \u201cNot listed\u201d for yourself.</p>' : '') +
    '<div class="utt-sheet-actions"><button type="button" class="utt-b" data-x="never">Don\u2019t show again</button>' +
    '<button type="button" class="utt-b utt-b-main" data-x="later">Got it</button></div></div>';
  o.addEventListener('click', function(ev){
    var t = ev.target.closest ? ev.target.closest('[data-x]') : null;
    if(!t && ev.target !== o) return;
    var x = t ? t.getAttribute('data-x') : 'later';
    lsSet(HINT_KEY, x === 'never' ? 'never' : String(Date.now() + 14 * 24 * 3600 * 1000));
    o.remove(); var p = document.querySelector('.utt-install'); if(p) p.remove();
  });
  document.body.appendChild(o);
}
window.addEventListener('beforeinstallprompt', function(e){ e.preventDefault(); deferredPrompt = e; showInstallPill(); });
window.addEventListener('appinstalled', function(){ var p = document.querySelector('.utt-install'); if(p) p.remove(); });

/* ---------- service worker: app shell only; update only when the person says so ---------- */
var swState = {supported: 'serviceWorker' in navigator, registered: false, error: '', updateReady: false};
var reloading = false, lastCheck = 0;
function showUpdate(worker){
  swState.updateReady = true;
  if(document.querySelector('.utt-update')) return;
  var bar = el('div', 'utt-update');
  bar.setAttribute('role', 'status');
  bar.innerHTML = '<span>An Under the Tree update is ready.</span>' +
    '<button type="button" class="utt-b utt-b-main" data-u="go">Update</button><button type="button" class="utt-b" data-u="later">Later</button>';
  bar.addEventListener('click', function(ev){
    var t = ev.target.closest ? ev.target.closest('[data-u]') : null; if(!t) return;
    if(t.getAttribute('data-u') === 'later'){ bar.remove(); return; }
    var busy = false; try { busy = !!(window.UTT && window.UTT.sheetOpen && window.UTT.sheetOpen()); } catch(e){}
    if(busy){ bar.querySelector('span').textContent = 'Finish or cancel what you\u2019re editing, then tap Update.'; return; }
    reloading = true; t.disabled = true;
    worker.postMessage({type: 'SKIP_WAITING'});
  });
  document.body.appendChild(bar);
}
function track(reg){
  if(reg.waiting && navigator.serviceWorker.controller) showUpdate(reg.waiting);
  reg.addEventListener('updatefound', function(){
    var w = reg.installing; if(!w) return;
    w.addEventListener('statechange', function(){
      if(w.state === 'installed' && navigator.serviceWorker.controller) showUpdate(w);
      if(w.state === 'redundant' && !swState.updateReady) warn('an update failed to install; still on build ' + BUILD);
    });
  });
  document.addEventListener('visibilitychange', function(){
    if(document.hidden || Date.now() - lastCheck < 30 * 60 * 1000) return;
    lastCheck = Date.now(); reg.update().catch(function(e){ warn('update check failed: ' + ((e && e.message) || e)); });
  });
}
function registerSW(){
  if(!swState.supported){ swState.error = 'not supported by this browser'; return; }
  var okOrigin = location.protocol === 'https:' || location.hostname === 'localhost' || location.hostname === '127.0.0.1';
  if(!okOrigin){ swState.error = 'needs https'; warn('service worker skipped: page is not on https'); return; }
  navigator.serviceWorker.addEventListener('controllerchange', function(){ if(reloading) location.reload(); });
  navigator.serviceWorker.register('service-worker.js', {scope: './', updateViaCache: 'none'}).then(function(reg){
    swState.registered = true; lastCheck = Date.now(); track(reg);
  }).catch(function(e){ swState.error = String((e && e.message) || e); warn('service worker registration failed: ' + swState.error); });
}

/* ---------- ask the browser to keep this site's storage (sign-in lives in localStorage) ---------- */
function askPersist(){
  try {
    if(!lsGet('utt.config') || !navigator.storage || !navigator.storage.persist) return;
    navigator.storage.persisted().then(function(p){ if(!p) return navigator.storage.persist(); })
      .catch(function(e){ warn('storage.persist failed: ' + ((e && e.message) || e)); });
  } catch(e){}
}

window.UTT_WEB = { build: BUILD, standalone: standalone, isIOS: isIOS, gate: gate, sw: swState, openInstallHelp: openInstallHelp };
window.addEventListener('load', function(){ registerSW(); showInstallPill(); askPersist(); setInterval(askPersist, 60000); });
})();
