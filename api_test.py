# -*- coding: utf-8 -*-
"""用真实 uid+idToken 验证 Dreamerland 业务 API"""
import json, urllib.request, ssl
ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
creds = json.load(open('D:/dreamerland-2api-app/creds.json'))
uid = creds['localId']; tok = creds['idToken']
print('uid:', uid)

def req(url, method='GET', body=None, auth=False):
    h = {'User-Agent':'Dreamerland/1.60.0','Content-Type':'application/json'}
    if auth: h['Authorization'] = 'Bearer ' + tok
    d = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=d, method=method, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=20, context=ctx) as resp:
            return resp.status, resp.read(1500)
    except urllib.error.HTTPError as e:
        return e.code, e.read(600)
    except Exception as e:
        return 'ERR', str(e)[:200].encode()

# 1. enhance-prompt (上一轮 User not found — 现在应该通)
s,b = req('https://apis.dreamerland.ai/enhance-prompt','POST',
          {'prompt':'a cat on a roof at sunset','uid':uid})
print('1 enhance-prompt:', s, b[:300])
# 2. 带鉴权的历史
s,b = req('https://apis.dreamerland.ai/list/history/%s?status=completed&page=1' % uid, auth=True)
print('2 history:', s, b[:300])
# 3. 无鉴权对照
s,b = req('https://apis.dreamerland.ai/list/history/%s' % uid)
print('3 history noauth:', s, b[:200])
