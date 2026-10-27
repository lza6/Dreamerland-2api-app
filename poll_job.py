# -*- coding: utf-8 -*-
import json, urllib.request, ssl, time, sys
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
creds=json.load(open('D:/dreamerland-2api-app/creds.json'))
uid=creds['localId']; tok=creds['idToken']
doc=sys.argv[1]
url='https://firestore.googleapis.com/v1/projects/dreamer-ai/databases/(default)/documents/users/%s/jobs/%s' % (uid,doc)
for i in range(30):
    r=urllib.request.Request(url,headers={'Authorization':'Bearer '+tok})
    with urllib.request.urlopen(r,timeout=20,context=ctx) as resp:
        j=json.loads(resp.read())
    st=j.get('fields',{}).get('status',{}).get('stringValue')
    print(time.strftime('%H:%M:%S'), 'status:', st)
    if st in ('completed','failed','error','cancelled'):
        print(json.dumps(j.get('fields',{}),indent=1,ensure_ascii=False)[:3000])
        break
    time.sleep(6)
