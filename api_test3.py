# -*- coding: utf-8 -*-
# Firestore 用 Bearer 头而非 query; 且 app 初始化时必然写自己的 user doc — 试带 auth 的写入/读取
import json, urllib.request, ssl
ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
creds = json.load(open('D:/dreamerland-2api-app/creds.json'))
uid = creds['localId']; tok = creds['idToken']

def fs(path, method='GET', body=None):
    url = 'https://firestore.googleapis.com/v1/projects/dreamer-ai/databases/(default)/documents/' + path
    h = {'Content-Type':'application/json','Authorization':'Bearer '+tok}
    d = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=d, method=method, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=20, context=ctx) as resp:
            return resp.status, resp.read(3000)
    except urllib.error.HTTPError as e:
        return e.code, e.read(400)
    except Exception as e:
        return 'ERR', str(e)[:200].encode()

# 带token读自己 user doc (app 会创建 users/{uid})
s,b = fs('users/%s' % uid)
print('user doc:', s, str(b[:400]))
# app 启动即写: 尝试创建自己的 user 文档 (模拟 app 行为)
s,b = fs('users/%s' % uid, 'PATCH', {'fields':{'uid':{'stringValue':uid},'appVersion':{'stringValue':'1.60.0'}}})
print('write user doc:', s, str(b[:300]))
# 再读
s,b = fs('users/%s' % uid)
print('reread:', s, str(b[:500]))
