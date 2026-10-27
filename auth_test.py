# -*- coding: utf-8 -*-
"""Firebase Auth REST 匿名注册 — Dreamerland dreamer-ai 项目
apiKey 来自 APK libRollingHunters.so 提取"""
import json, urllib.request, ssl, sys

ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
KEYS = [
    'AIzaSyCoLUy12KbmxMuOHVHT2zR8p6-r6It6low',
    'AIzaSyBbdlG-RVEOmY84ch5sxgNeXGV8ZpzaQNQ',
    'AIzaSyCvXZ4XQl0d6Z52HdXqeBeNwHWmS6fyoIo',
]
def post(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method='POST',
        headers={'Content-Type':'application/json','User-Agent':'Dreamerland/1.60.0 (Android)','X-Android-Package':'art.dreamerai.android'})
    try:
        with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b'{}')
    except Exception as e:
        return 'ERR', {'msg': str(e)[:200]}

for k in KEYS:
    s, j = post('https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=' + k,
                {'returnSecureToken': True})
    print(k[:12], s, str(j)[:200])
    if s == 200 and 'idToken' in j:
        print('\nSUCCESS with key', k)
        print(json.dumps({x: j[x] for x in ('idToken','refreshToken','localId','email') if x in j}, indent=1)[:800])
        open('D:/dreamerland-2api-app/creds.json','w').write(json.dumps(j))
        break
