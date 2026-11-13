"""Applies the web/PWA core changes to the 0.10.1 index.html. Every edit must match exactly once or the script stops."""
import sys, pathlib
src = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'); out = sys.argv[2]
EDITS = [
 # 1. Platform: web flag + standalone detection
 ("const Platform = {\n  isNative: !!Native,\n",
  "const Platform = {\n  isNative: !!Native,\n"
  "  /* web: true only in the web/PWA build (web/pwa.js sets window.UTT_WEB before this script). Android never has it. */\n"
  "  isWeb: !Native && !!window.UTT_WEB,\n"),
 # 2. copy: clipboard API fallback for Safari (web only) + copyText alias (0.10.1 bug: 'claimcode:copy' called an undefined Platform.copyText)
 ("  copy(text){\n    if(Native){ return Native.copyText(text) === true; }\n    try {\n      const t = document.createElement('textarea'); t.value = text; document.body.appendChild(t); t.select();\n      const ok = document.execCommand('copy'); t.remove(); return !!ok;\n    } catch(e){ return false; }\n  },\n",
  "  copy(text){\n    if(Native){ return Native.copyText(text) === true; }\n"
  "    /* web: the Clipboard API works in Safari and Chrome on https. It is asynchronous, so a later failure is reported loudly. */\n"
  "    if(navigator.clipboard && window.isSecureContext){\n"
  "      navigator.clipboard.writeText(String(text)).catch(() => { try { toast('Copy failed. Press and hold the text to select it instead.', 'err'); } catch(e){} });\n"
  "      return true;\n    }\n"
  "    try {\n      const t = document.createElement('textarea'); t.value = text; t.setAttribute('readonly', ''); t.style.fontSize = '16px'; document.body.appendChild(t); t.select();\n      const ok = document.execCommand('copy'); t.remove(); return !!ok;\n    } catch(e){ return false; }\n  },\n"
  "  /* 0.10.1 called Platform.copyText for setup codes but only copy() existed, so Copy threw. Same behaviour as copy(). */\n"
  "  copyText(text){ return this.copy(text); },\n"),
 # 3. About identifies the web build
 ("'<section class=\"panel\"><h3>About</h3><p class=\"hint\">Under the Tree ' + APP_VERSION + (Platform.isNative ? ' for Android' : ' web version') + '.</p>' +",
  "'<section class=\"panel\"><h3>About</h3><p class=\"hint\">Under the Tree ' + APP_VERSION + (Platform.isNative ? ' for Android' : (Platform.isWeb ? '<br>Web / PWA' + (window.UTT_WEB.standalone() ? ' (installed)' : ' (in the browser)') + ', build ' + esc(window.UTT_WEB.build) : ' web version')) + '.</p>' +"),
 # 4. Fill from link on the web: honest, non-alarming message; no scraping attempt
 ("if(!Platform.isNative){ setFill('warn', 'Filling from a link only works in the Android app. Type the details in below.'); return; }",
  "if(!Platform.isNative){ setFill('warn', 'We couldn\\u2019t fill this item automatically. You can still enter the details below.'); return; }"),
 # 5. boot: in the web build the opening scene and music wait for the first deliberate tap (browser audio rules)
 ("  applyTheme();\n  festive('snow');\n  intro();\n  ambStart();\n  startMusic(false);\n}",
  "  applyTheme();\n  festive('snow');\n"
  "  if(Platform.isWeb && typeof window.UTT_WEB.gate === 'function'){\n"
  "    ambStart();\n    window.UTT_WEB.gate(musicEnabled(), function(){ intro(); if(startMusic(false) && MUSIC.ctx && MUSIC.ctx.state === 'suspended'){ try { MUSIC.ctx.resume(); } catch(e){} } });\n"
  "    return;\n  }\n"
  "  intro();\n  ambStart();\n  startMusic(false);\n}"),
 # 6. expose sheetOpen so the web update banner never reloads over an open form
 ("  isOrganizerMember, isRemoved, meIsOrganizer, organizerCount, canManageFamily, connChip };",
  "  isOrganizerMember, isRemoved, meIsOrganizer, organizerCount, canManageFamily, connChip, sheetOpen };"),
  # 7. a family member's first name sat in a source comment; the web build is public, so keep it generic
 ("Chases Rudolph while Heather runs Classic Christmas", "Chases Rudolph while another person runs Classic Christmas"),
]
for old, new in EDITS:
    n = src.count(old)
    if n != 1: sys.exit('PATCH FAILED (%d matches): %r' % (n, old[:90]))
    src = src.replace(old, new)
pathlib.Path(out).write_text(src, encoding='utf-8')
print('patched', len(EDITS), 'edits ->', out)
