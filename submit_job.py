# -*- coding: utf-8 -*-
"""按 web 版真实 schema 提交生成 job 并轮询"""
import json, urllib.request, ssl, time, sys
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
creds=json.load(open('D:/dreamerland-2api-app/creds.json'))
uid=creds['localId']; tok=creds['idToken']

def fs(method, path, body=None):
    url='https://firestore.googleapis.com/v1/projects/dreamer-ai/databases/(default)/documents/'+path
    r=urllib.request.Request(url, data=json.dumps(body).encode() if body else None, method=method,
        headers={'Content-Type':'application/json','Authorization':'Bearer '+tok})
    with urllib.request.urlopen(r,timeout=25,context=ctx) as resp:
        return json.loads(resp.read())

job={'fields':{
 'version':{'stringValue':'1.40.0'},
 'prompt':{'stringValue':'a cute orange cat sitting on a windowsill, warm sunlight, anime style, masterpiece'},
 'negPrompt':{'stringValue':''},
 'task':{'stringValue':'txt2img'},
 'aspectRatio':{'stringValue':'square'},
 'ratio':{'stringValue':'square'},
 'styles':{'arrayValue':{'values':[]}},
 'steps':{'integerValue':'50'},
 'scale':{'doubleValue':1},
 'createdAt':{'integerValue':str(int(time.time()*1000))},
 'status':{'stringValue':'queueing'},
 'model':{'stringValue':'z_image_turbo'},
 'modelType':{'stringValue':'zimage'},
 'seed':{'integerValue':'0'},
 'img2img':{'booleanValue':False},
 'inpaint':{'booleanValue':False},
 'favourite':{'booleanValue':False},
 'hiresfix':{'booleanValue':False},
 'isVideo':{'booleanValue':False},
 'batch':{'integerValue':'1'},
 'web':{'booleanValue':True},
 'platform':{'stringValue':'web'},
 'folder':{'stringValue':''},
 'scheduler':{'stringValue':'euler'},
 'clipSkip':{'integerValue':'2'},
}}
j=fs('POST','users/%s/jobs' % uid, job)
name=j['name'].rsplit('/',1)[-1]
print('job id:', name)
# 轮询
url='https://firestore.googleapis.com/v1/projects/dreamer-ai/databases/(default)/documents/users/%s/jobs/%s' % (uid,name)
for i in range(40):
    time.sleep(6)
    r=urllib.request.Request(url,headers={'Authorization':'Bearer '+tok})
    with urllib.request.urlopen(r,timeout=20,context=ctx) as resp:
        cur=json.loads(resp.read())
    st=cur['fields'].get('status',{}).get('stringValue')
    print(time.strftime('%H:%M:%S'), st)
    if st not in ('queueing','processing','running'):
        print(json.dumps(cur['fields'],indent=1,ensure_ascii=False)[:4000])
        break
