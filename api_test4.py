# -*- coding: utf-8 -*-
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
            return resp.status, resp.read(8000)
    except urllib.error.HTTPError as e:
        return e.code, e.read(400)
    except Exception as e:
        return 'ERR', str(e)[:200].encode()

# 全量 user doc
s,b = fs('users/%s' % uid)
j = json.loads(b)
print('== FULL USER DOC ==')
print(json.dumps(j.get('fields',{}), indent=1, ensure_ascii=False)[:2000])
# 子集合 (任务一般在 users/{uid}/tasks 或 collection 里)
s,b = fs('users/%s?mask.fieldPaths=x' % uid)  # listCollectionIds needs special endpoint
# 用专门的 collectionId 端点
url='https://firestore.googleapis.com/v1/projects/dreamer-ai/databases/(default)/documents/users/%s:listCollectionIds' % uid
r=urllib.request.Request(url, data=b'{}', method='POST', headers={'Content-Type':'application/json','Authorization':'Bearer '+tok})
try:
    with urllib.request.urlopen(r, timeout=20, context=ctx) as resp:
        print('== SUBCOLLECTIONS ==', resp.read(500))
except urllib.error.HTTPError as e:
    print('subcoll err:', e.code, e.read(200))
