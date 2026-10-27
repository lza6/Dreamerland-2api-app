# -*- coding: utf-8 -*-
# 探生成任务提交: Firestore REST 直接读写 (dreamer-ai 项目, uid 可匿名读自己文档?)
import json, urllib.request, ssl
ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
creds = json.load(open('D:/dreamerland-2api-app/creds.json'))
uid = creds['localId']; tok = creds['idToken']

def fs(path, method='GET', body=None):
    url = 'https://firestore.googleapis.com/v1/projects/dreamer-ai/databases/(default)/documents/' + path
    if 'accessToken' not in path and '?' not in url:
        url += '?access_token=' + tok
    h = {'Content-Type':'application/json'}
    d = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=d, method=method, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=20, context=ctx) as resp:
            return resp.status, resp.read(2000)
    except urllib.error.HTTPError as e:
        return e.code, e.read(400)
    except Exception as e:
        return 'ERR', str(e)[:200].encode()

# 常见集合名探测 (只读)
for coll in ['users','user','profiles','tasks','task','generations','credits','devices','apk_users','users/%s' % uid]:
    s,b = fs(coll)
    print(coll, '->', s, str(b[:150]))
