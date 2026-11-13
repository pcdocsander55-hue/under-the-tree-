"""In-memory stand-in for Firebase Auth + Firestore REST, shared by every browser context in a test run.
It implements only what the app calls (signUp, token refresh, GET doc, GET list, :commit) and a SMALL subset
of the real rules, to check the web client's behaviour. It is NOT a substitute for the Firestore rules emulator."""
import hashlib, json, re, time, uuid
from urllib.parse import urlparse, unquote
BASE = '/v1/projects/under-the-tree-1ee02/databases/(default)/documents'
def err(status, code, msg): return status, {'error': {'code': status, 'status': code, 'message': msg}}
def val(v):
    if v is None: return None
    for k in ('stringValue', 'booleanValue', 'timestampValue'):
        if k in v: return v[k]
    if 'integerValue' in v: return int(v['integerValue'])
    if 'doubleValue' in v: return v['doubleValue']
    if 'nullValue' in v: return None
    if 'arrayValue' in v: return [val(x) for x in v['arrayValue'].get('values', [])]
    if 'mapValue' in v: return {k: val(x) for k, x in v['mapValue'].get('fields', {}).items()}
    return v
class MockFirebase:
    def __init__(self):
        self.docs = {}; self.log = []; self.signups = 0
    # ---- helpers
    def access_member(self, uid, fam):
        d = self.docs.get('%s/access/%s' % (fam, uid)); return val(d['fields'].get('memberId')) if d and 'memberId' in d['fields'] else None
    def denied_read(self, uid, path):
        m = re.match(r'(families/[^/]+)/hidden/([^/]+)(/|$)', path)
        return bool(m and self.access_member(uid, m.group(1)) == m.group(2))
    # ---- routing
    def handle(self, method, url, headers, body):
        u = urlparse(url); host = u.netloc
        if host == 'identitytoolkit.googleapis.com' and u.path.endswith('accounts:signUp'):
            self.signups += 1; uid = 'u' + uuid.uuid4().hex[:20]
            return 200, {'localId': uid, 'idToken': 'tok-' + uid, 'refreshToken': 'ref-' + uid, 'expiresIn': '3600'}
        if host == 'securetoken.googleapis.com':
            rt = dict(x.split('=', 1) for x in (body or '').split('&')).get('refresh_token', '')
            uid = unquote(rt)[4:]
            return 200, {'id_token': 'tok-' + uid, 'refresh_token': rt, 'user_id': uid, 'expires_in': '3600'}
        if host != 'firestore.googleapis.com': return err(404, 'NOT_FOUND', 'unknown host')
        auth = (headers.get('authorization') or '')
        if not auth.startswith('Bearer tok-'): return err(401, 'UNAUTHENTICATED', 'no token')
        uid = auth[len('Bearer tok-'):]
        path = unquote(u.path)
        if not path.startswith(BASE): return err(404, 'NOT_FOUND', 'bad path')
        rest = path[len(BASE):]
        if method == 'POST' and rest == ':commit': return self.commit(uid, json.loads(body or '{}'))
        rel = rest.lstrip('/')
        self.log.append((uid, method, rel))
        if method != 'GET': return err(400, 'INVALID_ARGUMENT', 'unsupported')
        if self.denied_read(uid, rel): return err(403, 'PERMISSION_DENIED', 'Missing or insufficient permissions.')
        segs = rel.split('/')
        if len(segs) % 2 == 0:
            d = self.docs.get(rel)
            return (200, d) if d else err(404, 'NOT_FOUND', 'No document to get. Path ' + rel)
        pre = rel + '/'
        docs = [d for p, d in sorted(self.docs.items()) if p.startswith(pre) and '/' not in p[len(pre):]]
        return 200, ({'documents': docs} if docs else {})
    def commit(self, uid, body):
        writes = body.get('writes', []); new = dict(self.docs); now = time.strftime('%Y-%m-%dT%H:%M:%S.000000Z', time.gmtime())
        paths = []
        for w in writes:
            name = w.get('update', {}).get('name') or w.get('delete'); rel = name.split('/documents/', 1)[1]; paths.append(rel)
            self.log.append((uid, 'WRITE', rel))
            pre = w.get('currentDocument', {})
            if 'exists' in pre:
                if pre['exists'] and rel not in new: return err(404, 'NOT_FOUND', 'No document to update: ' + rel)
                if not pre['exists'] and rel in new: return err(409, 'ALREADY_EXISTS', 'Document already exists: ' + rel)
            if 'delete' in w: new.pop(rel, None); continue
            fields = w['update'].get('fields', {})
            if 'updateMask' in w and rel in new:
                merged = dict(new[rel]['fields'])
                for fp in w['updateMask']['fieldPaths']:
                    if fp in fields: merged[fp] = fields[fp]
                    else: merged.pop(fp, None)
                fields = merged
            for t in w.get('updateTransforms', []): fields[t['fieldPath']] = {'timestampValue': now}
            new[rel] = {'name': name, 'fields': fields, 'createTime': self.docs.get(rel, {}).get('createTime', now), 'updateTime': now}
        # ---- rule subset: Gift Ideas can't be written by their recipient
        for rel in paths:
            m = re.match(r'(families/[^/]+)/hidden/([^/]+)/(giftIdeas|ideaReservations)/', rel)
            if m and self.access_member(uid, m.group(1)) == m.group(2): return err(403, 'PERMISSION_DENIED', 'recipient may not touch own ideas')
        # ---- rule subset: a managed profile (managerIds) moves to a new sign-in only with its valid one-time setup code
        for rel in paths:
            m = re.match(r'(families/[^/]+)/members/([^/]+)$', rel)
            if not m or rel not in self.docs: continue
            old, nw = self.docs[rel]['fields'], new.get(rel, {}).get('fields', {})
            if val(nw.get('uid')) == uid and val(old.get('uid')) != uid and val(old.get('managerIds')):
                cp = '%s/memberClaims/%s' % (m.group(1), m.group(2)); c_old = self.docs.get(cp); c_new = new.get(cp)
                if not c_old or cp not in paths or val(c_old['fields'].get('usedBy')): return err(403, 'PERMISSION_DENIED', 'claim needs a live setup code')
                tok = val(c_new['fields'].get('usedToken')) if c_new else None
                if not tok or hashlib.sha256(tok.encode()).hexdigest() != val(c_old['fields'].get('tokenHash')):
                    return err(403, 'PERMISSION_DENIED', 'setup code hash mismatch')
        self.docs = new
        return 200, {'writeResults': [{'updateTime': now} for _ in writes], 'commitTime': now}
    # ---- playwright glue
    def route(self, route, request):
        st, data = self.handle(request.method, request.url, {k.lower(): v for k, v in request.headers.items()}, request.post_data)
        route.fulfill(status=st, content_type='application/json', body=json.dumps(data),
                      headers={'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': '*', 'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'})
