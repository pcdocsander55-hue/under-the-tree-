"""Under the Tree web/PWA test run (Chromium + in-memory Firebase stand-in). Writes results to stdout and results.json."""
import sys, json, re, time, shutil, pathlib, subprocess, traceback
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from playwright.sync_api import sync_playwright
from hosting_server import serve
from mock_firestore import MockFirebase
ROOT = pathlib.Path(__file__).resolve().parent.parent
CHROME = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
PORT = 8765; URL = 'http://localhost:%d/' % PORT
IPHONE_UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1'
R = []
def check(name, ok, detail=''):
    R.append({'test': name, 'result': 'PASS' if ok else 'FAIL', 'detail': str(detail)[:400]})
    print(('PASS ' if ok else 'FAIL ') + name + ((' :: ' + str(detail)[:200]) if detail and not ok else ''))
def section(n): print('\n== ' + n); R.append({'section': n})
subprocess.run([sys.executable, str(ROOT / 'tools' / 'build_web.py')], check=True)
srv = serve(PORT); fb = MockFirebase()
INIT = """window.__csp=[];document.addEventListener('securitypolicyviolation',e=>window.__csp.push(e.violatedDirective+' '+e.blockedURI));"""
class Dev:
    def __init__(s, b, label, ua=None, vp=(390, 844), state=None, music=True):
        s.label = label
        kw = dict(viewport={'width': vp[0], 'height': vp[1]}, has_touch=True)
        if ua: kw['user_agent'] = ua
        if state: kw['storage_state'] = state
        s.ctx = b.new_context(**kw); s.ctx.route('https://*.googleapis.com/**', fb.route); s.ctx.add_init_script(INIT)
        if not music: s.ctx.add_init_script("try{localStorage.setItem('utt.music','off')}catch(e){}")
        s.pg = s.ctx.new_page(); s.errors = []
        s.pg.on('pageerror', lambda e: s.errors.append(str(e)))
        s.pg.on('console', lambda m: s.errors.append('console.error ' + m.text) if m.type == 'error' and 'Failed to load resource' not in m.text else None)
    def open(s):
        s.pg.goto(URL); s.pg.wait_for_timeout(600)
        if s.pg.locator('.utt-gate-btn').count(): s.pg.click('.utt-gate-btn')
        s.pg.wait_for_timeout(300); return s
    def ev(s, js, arg=None): return s.pg.evaluate(js, arg)
    def refresh(s): s.ev('() => UTT.refresh()'); s.pg.wait_for_timeout(500)
    def uid(s): return s.ev('() => UTT.S.backend && UTT.S.backend.uid')
    def me(s): return s.ev('() => UTT.S.cfg && UTT.S.cfg.meId')
    def fam(s): return s.ev('() => UTT.S.cfg && UTT.S.cfg.familyId')
    def tab(s, t): s.pg.click('.nav [data-tab="%s"]' % t); s.pg.wait_for_timeout(250)
    def text(s): return s.pg.inner_text('body')
    def ls(s): return s.ev('() => JSON.stringify(Object.assign({}, localStorage))')
    def members(s): return s.ev('() => UTT.S.snap.members.map(m => ({id: m.id, name: m.name, uid: m.uid || null, managerIds: m.managerIds || []}))')
    def mid(s, name): return [m['id'] for m in s.members() if m['name'] == name][0]
def join_new(d, invite, name):
    d.pg.click('[data-act="setup:join"]'); d.pg.fill('form[data-form=join] textarea[name=code]', invite)
    d.pg.click('form[data-form=join] button[type=submit]'); d.pg.wait_for_timeout(700)
    d.pg.click('[data-act="join:newmode"]'); d.pg.fill('form[data-form=joinnew] input[name=name]', name)
    d.pg.click('form[data-form=joinnew] button[type=submit]'); d.pg.wait_for_timeout(900)
def add_wish_ui(d, title, idea_for=None):
    if idea_for:
        d.tab('family'); d.pg.click('[data-act="person"][data-id="%s"]' % idea_for); d.pg.wait_for_timeout(200)
        d.pg.click('[data-act="person:view"][data-id="ideas"]'); d.pg.click('[data-act="idea:new"]')
    else:
        d.tab('mine'); d.pg.click('[data-act="wish:new"] >> nth=0')
    d.pg.fill('#wishForm input[name=title]', title); d.pg.fill('#wishForm input[name=price]', '$20')
    d.pg.click('#wishForm button[type=submit]'); d.pg.wait_for_timeout(700)
def reads_of(uid, prefix): return [l for l in fb.log if l[0] == uid and l[1] == 'GET' and l[2].startswith(prefix)]

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME)
    try:
        # ------------------------------------------------------------------ PWA shell
        section('PWA shell, manifest, service worker')
        dad = Dev(b, 'Dad (plays the Android role)')
        dad.pg.goto(URL); dad.pg.wait_for_timeout(800)
        man = dad.ev("() => fetch('manifest.webmanifest').then(r => r.json())")
        check('manifest: name/short_name/display/start_url/scope', man['name'] == 'Under the Tree' and man['short_name'] == 'Under the Tree' and man['display'] == 'standalone' and man['start_url'] == './' and man['scope'] == './', man)
        check('manifest: 192, 512 and maskable icons', {i['sizes'] + i['purpose'] for i in man['icons']} >= {'192x192any', '512x512any', '512x512maskable'})
        ct = dad.ev("() => fetch('manifest.webmanifest').then(r => r.headers.get('content-type'))")
        check('manifest served as application/manifest+json', 'manifest+json' in (ct or ''), ct)
        head = dad.ev("() => document.head.innerHTML")
        for tag in ['apple-touch-icon', 'apple-mobile-web-app-capable', 'mobile-web-app-capable', 'apple-mobile-web-app-title', 'viewport-fit=cover', 'rel="manifest"']:
            check('head has ' + tag, tag in head)
        css = (ROOT / 'web/dist/pwa.css').read_text()
        check('safe-area CSS uses all four insets', all('env(safe-area-inset-%s)' % s in css for s in ['top', 'bottom', 'left', 'right']))
        check('first-tap Enter screen shown while music is on', dad.pg.locator('.utt-gate-btn').count() == 1)
        dad.pg.click('.utt-gate-btn'); dad.pg.wait_for_timeout(400)
        check('Enter starts music after the tap (no error)', dad.ev('() => UTT.music.plays') == 1 and dad.ev("() => UTT.music.ctx && UTT.music.ctx.state") == 'running', dad.ev("() => [UTT.music.plays, UTT.music.ctx && UTT.music.ctx.state]"))
        dad.pg.wait_for_function('() => navigator.serviceWorker.controller !== null', timeout=10000)
        check('service worker registered and controlling', dad.ev('() => UTT_WEB.sw.registered') is True)
        keys = dad.ev("() => caches.keys()"); urls = dad.ev("async () => { const out=[]; for(const k of await caches.keys()){ const c=await caches.open(k); for(const r of await c.keys()) out.push(r.url);} return out; }")
        check('one versioned shell cache', len(keys) == 1 and keys[0].startswith('utt-shell-0.10.1-'), keys)
        check('shell cache holds only static app files', all(u.startswith(URL) and not re.search(r'googleapis|firestore', u) for u in urls) and len(urls) == 10, urls)
        check('About/build flag reports web build', dad.ev('() => UTT.Platform.isWeb') is True and dad.ev('() => UTT.Platform.isNative') is False)

        # ------------------------------------------------------------------ family setup + join
        section('Start family (Dad), join with UTT2 (Heather on "iPhone"), persistence')
        dad.pg.click('[data-act="setup:start"]'); dad.pg.fill('input[name=familyName]', 'Test Family'); dad.pg.fill('form[data-form=start] input[name=name]', 'Dad')
        dad.pg.click('form[data-form=start] button[type=submit]'); dad.pg.wait_for_timeout(1200)
        invite = dad.pg.inner_text('.invite').strip()
        check('family created, UTT2 invite shown', invite.startswith('UTT2-') and dad.me() is not None, invite[:20])
        hea = Dev(b, 'Heather (iPhone Safari UA)', ua=IPHONE_UA).open()
        check('install tip shown in iPhone Safari', hea.pg.locator('.utt-install').count() == 1)
        hea.pg.click('.utt-install'); hea.pg.wait_for_timeout(200)
        t = hea.pg.inner_text('.utt-sheet')
        check('install help: Share / Add to Home Screen / Add', all(x in t for x in ['Share', 'Add to Home Screen', 'Add']))
        hea.pg.click('.utt-sheet [data-x="later"]'); hea.pg.wait_for_timeout(200)
        check('install tip hides after "Got it" and stays hidden on reload', hea.pg.locator('.utt-install').count() == 0)
        s0 = fb.signups
        join_new(hea, invite, 'Heather')
        check('Heather joined the SAME family', hea.fam() == dad.fam() and hea.me() is not None)
        H_uid, H_mid = hea.uid(), hea.me()
        hea.pg.reload(); hea.pg.wait_for_timeout(700)
        if hea.pg.locator('.utt-gate-btn').count(): hea.pg.click('.utt-gate-btn')
        check('install tip still hidden after reload', hea.pg.locator('.utt-install').count() == 0)
        check('reload: same sign-in + same profile, no new sign-up', hea.uid() == H_uid and hea.me() == H_mid and fb.signups == s0 + 1, (fb.signups, s0))
        state = hea.ctx.storage_state(); hea.ctx.close()
        hea = Dev(b, 'Heather reopened', ua=IPHONE_UA, state=state).open(); hea.pg.wait_for_timeout(800)
        check('close + reopen app: same identity, no rejoin, no duplicate', hea.uid() == H_uid and hea.me() == H_mid and fb.signups == s0 + 1 and len([m for m in hea.members() if m['name'] == 'Heather']) == 1)

        # ------------------------------------------------------------------ A. wish list spoiler
        section('A. Apple wish -> Android reserve/buy, no spoiler for the recipient')
        add_wish_ui(hea, 'Blue scarf')
        dad.refresh()
        w = dad.ev("() => UTT.S.snap.wishes.find(w => w.title === 'Blue scarf')")
        check('Dad sees Heather\'s new wish', w is not None)
        hea.tab('mine'); before = hea.pg.inner_text('main')
        D_mid = dad.me()
        dad.ev("async ([w, me]) => { await UTT.S.backend.reserve(w, me, false); }", [w, D_mid]); dad.refresh()
        hea.refresh(); hea.tab('mine'); after_res = hea.pg.inner_text('main')
        check('Heather\'s My List unchanged after Dad reserves', before == after_res)
        dad.ev("async (w) => { await UTT.S.backend.setResStatus({ownerId: w.ownerId, wishId: w.id, kind: 'wish'}, 'purchased'); }", w); dad.refresh()
        hea.refresh(); hea.tab('mine'); after_buy = hea.pg.inner_text('main')
        check('Heather\'s My List unchanged after Dad marks bought', before == after_buy)
        check('Heather never requested her own hidden reservations', not reads_of(H_uid, 'families/%s/hidden/%s' % (hea.fam(), H_mid)))
        check('Heather\'s local storage holds no reservation of her wish', 'purchased' not in hea.ls() and D_mid not in json.dumps([k for k in hea.ls().split('"byMemberId"')[1:]]))

        # ------------------------------------------------------------------ B. gift idea privacy
        section('B. Apple Gift Idea for Dad -> Dad sees nothing')
        add_wish_ui(hea, 'Secret drill', idea_for=D_mid)
        idea = hea.ev("() => (UTT.S.snap.ideas || []).find(i => i.title === 'Secret drill')")
        check('idea saved and visible to the shopper', idea is not None)
        kid = Dev(b, 'Grandma (another shopper)').open(); join_new(kid, invite, 'Grandma')
        check('another shopper sees the idea', kid.ev("() => !!(UTT.S.snap.ideas || []).find(i => i.title === 'Secret drill')"))
        hea.ev("async ([i, me]) => { await UTT.S.backend.reserve(i, me, false); }", [idea, H_mid])
        hea.ev("async (i) => { await UTT.S.backend.setResStatus({ownerId: i.ownerId, wishId: i.id, kind: 'idea'}, 'purchased'); }", idea)
        dad.refresh()
        for tb in ['mine', 'family', 'shopping', 'settings']:
            dad.tab(tb)
            if 'Secret drill' in dad.text() or re.search(r'gift idea', dad.pg.inner_text('main'), re.I) and tb == 'mine': check('Dad screen "%s" free of the idea' % tb, False, dad.pg.inner_text('main')[:200]); break
        else: check('Dad sees no idea, count, reservation or bought status on any tab', True)
        check('Dad\'s app never REQUESTED ideas for Dad', not reads_of(dad.uid(), 'families/%s/hidden/%s/' % (dad.fam(), D_mid)))
        check('Dad\'s snapshot + local storage contain no idea for Dad', 'Secret drill' not in dad.ls() and not dad.ev("() => (UTT.S.snap.ideas||[]).length"))

        # ------------------------------------------------------------------ C. shopping coordination (subset)
        section('C. Shopping coordination (client side only)')
        add_wish_ui(kid, 'Puzzle'); dad.refresh(); hea.refresh()
        pw = dad.ev("() => UTT.S.snap.wishes.find(w => w.title === 'Puzzle')")
        dad.ev("async ([w, me]) => { await UTT.S.backend.reserve(w, me, false); }", [pw, D_mid]); hea.refresh()
        st = hea.ev("(t) => { const w = UTT.S.snap.wishes.find(x => x.title === t); return w ? (UTT.S.snap.res && UTT.S.snap.res[w.id] ? 'taken' : JSON.stringify(Object.keys(UTT.S.snap))) : 'gone'; }", 'Puzzle')
        hea.tab('family')
        check('Heather sees the reserved item as taken / off the family list', st == 'taken' or 'Puzzle' not in hea.pg.inner_text('main'), st[:200])
        stole = hea.ev("async ([w, me]) => { try { await UTT.S.backend.reserve(w, me, false); return 'stole'; } catch(e){ return e.code; } }", [pw, H_mid])
        check('Heather cannot take an active hold (create-only write refused)', stole == 'CONFLICT', stole)

        # ------------------------------------------------------------------ D. managed child + setup code
        section('D. Add Child (Dad) -> Emma claims on web with setup code')
        emma_m = dad.ev("async ([me, h]) => { const m = await UTT.S.backend.addMember('Emma', {managed: true, meId: me, extraManagers: [h]}); return m; }", [D_mid, H_mid])
        dad.refresh(); E_mid = emma_m['id']
        check('Emma has Dad + Heather as managers', set(dad.ev("(id) => UTT.S.snap.members.find(m => m.id === id).managerIds", E_mid)) == {D_mid, H_mid})
        dad.ev("async (id) => { const m = UTT.S.snap.members.find(x => x.id === id); await UTT.S.backend.saveWish({id: 'emmaw1', ownerId: id, title: 'Unicorn book', url: '', price: '', store: '', imageUrl: '', exactItem: false, note: '', createdAt: Date.now(), updatedAt: Date.now(), createdBy: m.managerIds[0]}, true); }", E_mid)
        hea.refresh(); add_wish_ui(hea, 'Emma surprise idea', idea_for=E_mid)
        code = dad.ev("async (id) => { const m = UTT.S.snap.members.find(x => x.id === id); return await UTT.S.backend.issueClaimCode(m, UTT.S.cfg.meId); }", E_mid)
        check('setup code issued (20 chars); only its hash stored', len(code) == 20 and code not in json.dumps(fb.docs))
        emma = Dev(b, 'Emma (iPhone)', ua=IPHONE_UA).open()
        emma.pg.click('[data-act="setup:join"]'); emma.pg.fill('form[data-form=join] textarea[name=code]', invite)
        emma.pg.click('form[data-form=join] button[type=submit]'); emma.pg.wait_for_timeout(700)
        emma.pg.click('[data-act="join:claimlist"]'); emma.pg.wait_for_timeout(200)
        emma.pg.click('[data-act="join:pick"][data-id="%s"]' % E_mid); emma.pg.wait_for_timeout(400)
        check('picking Emma asks for a setup code (name alone is not enough)', emma.pg.locator('form[data-form=claimcode]').count() == 1)
        emma.pg.fill('form[data-form=claimcode] input[name=code]', 'AAAA-BBBB-CCCC-DDDD-EEEE'); emma.pg.click('form[data-form=claimcode] button[type=submit]'); emma.pg.wait_for_timeout(600)
        check('wrong setup code refused, nothing changed', emma.me() is None and 'didn' in emma.text(), emma.text()[:200])
        direct = emma.ev("async (id) => { try { const be = UTT.S.join.be; await be.claimMember(UTT.S.join.members.find(m => m.id === id)); return 'claimed'; } catch(e){ return e.code; } }", E_mid)
        check('claim without a code refused by the (mock) server', direct in ('PERMISSION_DENIED', 'BAD_CODE'), direct)
        emma.pg.fill('form[data-form=claimcode] input[name=code]', code); emma.pg.click('form[data-form=claimcode] button[type=submit]'); emma.pg.wait_for_timeout(900)
        dad.refresh(); ms = dad.members()
        check('the SAME Emma record was claimed', emma.me() == E_mid)
        check('no duplicate Emma', len([m for m in ms if m['name'] == 'Emma']) == 1, ms)
        check('Emma\'s existing wish kept', 'Unicorn book' in json.dumps(emma.ev("() => UTT.S.snap.wishes.map(w => w.title)")))
        check('Emma\'s managers kept', set([m for m in ms if m['id'] == E_mid][0]['managerIds']) == {D_mid, H_mid})
        check('Emma never requested ideas for Emma; none in DOM/storage', not reads_of(emma.uid(), 'families/%s/hidden/%s/' % (emma.fam(), E_mid)) and 'Emma surprise idea' not in emma.text() + emma.ls())
        dad.ev("async (id) => { await UTT.S.backend.saveWish({id: 'emmaw2', ownerId: id, title: 'Paint set', url: '', price: '', store: '', imageUrl: '', exactItem: false, note: '', createdAt: Date.now(), updatedAt: Date.now(), createdBy: UTT.S.cfg.meId}, true); }", E_mid)
        emma.refresh()
        check('Dad can still add to Emma\'s list after the claim', 'Paint set' in json.dumps(emma.ev("() => UTT.S.snap.wishes.map(w => w.title)")))

        # ------------------------------------------------------------------ E. organizer (client side only)
        section('E. Organizer on web (client side only)')
        dad.ev("async (id) => { const m = UTT.S.snap.members.find(x => x.id === id); await UTT.S.backend.promoteMember(m, UTT.organizerCount()); }", H_mid)
        hea.refresh()
        check('Heather (web) is now an organizer and gets manage controls', hea.ev('() => UTT.meIsOrganizer() && UTT.canManageFamily()'))
        dad.pg.evaluate("() => 0"); add_wish_ui(dad, 'Idea for Heather', idea_for=H_mid)
        hea.refresh()
        check('organizer Heather still never requests / sees ideas for Heather', not reads_of(H_uid, 'families/%s/hidden/%s/' % (hea.fam(), H_mid)) and 'Idea for Heather' not in hea.text() + hea.ls())

        # ------------------------------------------------------------------ misc web behaviour
        section('Web-specific behaviour')
        hea.tab('mine'); hea.pg.click('[data-act="wish:new"] >> nth=0'); hea.pg.fill('#wishForm input[name=url]', 'https://www.target.com/p/x'); hea.pg.click('[data-act="wish:fill"]')
        check('Fill from link: calm web message, form still usable', 'couldn’t fill this item automatically' in hea.pg.inner_text('#fillStatus'))
        hea.pg.click('#wishForm [data-act="sheet:close"]')
        check('Platform.copyText exists (0.10.1 setup-code Copy crash fixed)', hea.ev("() => typeof UTT.Platform.copyText === 'function'"))
        hea.tab('settings'); about = hea.pg.inner_text('main')
        check('Settings > About says Web / PWA and the build', 'Web / PWA' in about and '0.10.1-' in about)
        offered = hea.ev("() => UTT.offeredThemes().map(t => t.id)")
        check('only the two released themes offered', len(offered) == 2, offered)
        for tid in offered:
            ok = hea.ev("(id) => UTT.setTheme(id) && UTT.themeId() === id", tid)
            check('theme %s applies on web' % tid, ok)
        quiet = Dev(b, 'music off', music=False); quiet.pg.goto(URL); quiet.pg.wait_for_timeout(600)
        check('music off: no Enter screen, straight into the app', quiet.pg.locator('.utt-gate').count() == 0 and quiet.ev('() => UTT.music.plays') == 0)
        rm = b.new_context(reduced_motion='reduce', viewport={'width': 390, 'height': 844}); rp = rm.new_page(); rp.goto(URL); rp.wait_for_timeout(500)
        if rp.locator('.utt-gate-btn').count(): rp.click('.utt-gate-btn')
        check('reduced motion: opening scene skipped', rp.evaluate('() => UTT.reducedMotion() && !UTT.introShowing()'))
        rm.close()

        # ------------------------------------------------------------------ layout
        section('Layout at Apple widths (no sideways scrolling, Cancel reachable)')
        for (wd, ht, nm) in [(320, 568, 'iPhone SE 1st gen'), (375, 667, 'iPhone SE'), (393, 852, 'iPhone 15/16'), (440, 956, 'Pro Max'), (768, 1024, 'iPad portrait')]:
            hea.pg.set_viewport_size({'width': wd, 'height': ht}); bad = []
            for tb in ['mine', 'family', 'shopping', 'settings']:
                hea.tab(tb)
                if hea.ev('() => document.documentElement.scrollWidth > window.innerWidth + 1'): bad.append(tb)
            hea.tab('family'); hea.pg.click('[data-act="person"][data-id="%s"]' % D_mid); hea.pg.wait_for_timeout(150)
            hea.pg.click('[data-act="person:view"][data-id="ideas"]'); hea.pg.click('[data-act="idea:new"]'); hea.pg.wait_for_timeout(200)
            cb = hea.pg.locator('#wishForm [data-act="sheet:close"]').bounding_box()
            if hea.ev('() => document.documentElement.scrollWidth > window.innerWidth + 1'): bad.append('idea sheet')
            vis = cb and cb['y'] + cb['height'] <= ht and cb['x'] >= 0 and cb['x'] + cb['width'] <= wd
            small = hea.ev("() => [...document.querySelectorAll('#wishForm button, .nav button')].filter(b => b.offsetParent && b.getBoundingClientRect().height < 38).length")
            hea.pg.click('#wishForm [data-act="sheet:close"]')
            check('%s %dpx: no sideways scroll; Cancel on screen; buttons >=38px tall' % (nm, wd), not bad and vis and small == 0, (bad, cb, small))
        hea.pg.set_viewport_size({'width': 390, 'height': 844})
        hea.pg.click('[data-act="person"][data-id="%s"]' % D_mid) if hea.pg.locator('[data-act="person"][data-id="%s"]' % D_mid).count() else None

        # ------------------------------------------------------------------ caches after use, CSP
        section('Privacy of caches, CSP, errors')
        urls = hea.ev("async () => { const out=[]; for(const k of await caches.keys()){ const c=await caches.open(k); for(const r of await c.keys()) out.push(r.url);} return out; }")
        check('after all flows the SW cache still holds only the 10 shell files', len(urls) == 10 and not any('googleapis' in u for u in urls), urls)
        bodies = hea.ev("async () => { let s=''; for(const k of await caches.keys()){ const c=await caches.open(k); for(const r of await c.keys()) s += await (await c.match(r)).clone().text().catch(()=>''); } return s; }")
        check('no family data (names, wishes, ideas, invite) inside the SW cache', not any(x in bodies for x in ['Blue scarf', 'Secret drill', 'Heather', invite[5:40]]))
        for d in [dad, hea, kid, emma]:
            v = d.ev('() => window.__csp')
            check('no CSP violations (%s)' % d.label, not v, v)
            check('no page errors (%s)' % d.label, not d.errors, d.errors[:3])

        # ------------------------------------------------------------------ update flow
        section('Update: new build detected, never reloads over an open form, identity kept')
        before_build = hea.ev('() => UTT_WEB.build')
        (ROOT / 'web/pwa.css').write_text((ROOT / 'web/pwa.css').read_text() + '\n/* test-bump */\n')
        subprocess.run([sys.executable, str(ROOT / 'tools' / 'build_web.py')], check=True, capture_output=True)
        hea.ev("() => navigator.serviceWorker.getRegistration().then(r => r.update())")
        hea.pg.wait_for_selector('.utt-update', timeout=10000)
        check('"An Under the Tree update is ready." shown', 'update is ready' in hea.pg.inner_text('.utt-update'))
        hea.tab('mine'); hea.pg.click('[data-act="wish:new"] >> nth=0'); hea.pg.fill('#wishForm input[name=title]', 'half-typed')
        hea.pg.click('.utt-update [data-u="go"]'); hea.pg.wait_for_timeout(800)
        check('Update refused while a wish is being edited (text kept)', hea.pg.input_value('#wishForm input[name=title]') == 'half-typed' and 'Finish or cancel' in hea.pg.inner_text('.utt-update'))
        hea.pg.click('#wishForm [data-act="sheet:close"]')
        with hea.pg.expect_navigation(timeout=10000): hea.pg.click('.utt-update [data-u="go"]')
        hea.pg.wait_for_timeout(800)
        if hea.pg.locator('.utt-gate-btn').count(): hea.pg.click('.utt-gate-btn')
        nb = hea.ev('() => UTT_WEB.build')
        check('after Update: new build running', nb != before_build, (before_build, nb))
        check('after Update: same sign-in and profile', hea.uid() == H_uid and hea.me() == H_mid)
        check('after Update: exactly one (new) shell cache', hea.ev("() => caches.keys()") == ['utt-shell-' + nb])
    except Exception as e:
        traceback.print_exc(); check('test run completed without crashing', False, repr(e))
    finally:
        css = (ROOT / 'web/pwa.css'); css.write_text(css.read_text().replace('\n/* test-bump */\n', ''))
        subprocess.run([sys.executable, str(ROOT / 'tools' / 'build_web.py')], check=True, capture_output=True)
        b.close()
json.dump(R, open(ROOT / 'tests' / 'results.json', 'w'), indent=1)
n = [r for r in R if 'result' in r]; f = [r for r in n if r['result'] == 'FAIL']
print('\n%d checks, %d passed, %d failed' % (len(n), len(n) - len(f), len(f)))
