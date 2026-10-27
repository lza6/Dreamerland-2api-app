# -*- coding: utf-8 -*-
"""Dreamerland 2API — 生产级客户端库
协议: Firebase 匿名Auth → Firestore users/{uid}/jobs 任务队列 → webhook worker → 图片URL
用法:
    from dreamerland_api import DreamerlandClient
    c = DreamerlandClient()
    img = c.generate('a cat', model='z_image_turbo', wait=True)
"""
import json, urllib.request, ssl, time, uuid

CTX = ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
FIREBASE_KEY = 'AIzaSyBbdlG-RVEOmY84ch5sxgNeXGV8ZpzaQNQ'   # dreamer-ai 项目有效 key
PROJECT = 'dreamer-ai'
FS = 'https://firestore.googleapis.com/v1/projects/%s/databases/(default)/documents' % PROJECT
VERSION = '1.40.0'

MODELS = {
  # type -> models (从 web bundle 提取的完整模型库, 常用子集)
  'z_image_turbo': ('zimage', True), 'z_image_moody_mix': ('zimage', True),
  'flux2_klein': ('flux2', True), 'nano_banana': ('nano_banana', False),
  'nano_banana_2': ('nano_banana', False), 'nano_banana_pro': ('nano_banana', False),
  'seedream45': ('seedream', False), 'seedream50lite': ('seedream', False),
  'seedream50pro': ('seedream', False), 'gpt_image_2': ('gpt_image', False),
  'gpt_image_25': ('gpt_image', False), 'krea2_turbo': ('krea2', True),
}

class DreamerlandClient:
    def __init__(self, creds_path=None):
        self.creds_path = creds_path or 'dreamerland_creds.json'
        self._load_or_signup()

    def _load_or_signup(self):
        try:
            j = json.load(open(self.creds_path))
            if j.get('expiresAt', 0) > time.time() + 300:
                self.uid, self.tok = j['localId'], j['idToken']; return
        except Exception: pass
        req = urllib.request.Request(
            'https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=' + FIREBASE_KEY,
            data=b'{"returnSecureToken":true}', method='POST',
            headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req, timeout=30, context=CTX) as r:
            j = json.loads(r.read())
        j['expiresAt'] = time.time() + int(j.get('expiresIn','3600')) - 600
        json.dump(j, open(self.creds_path,'w'))
        self.uid, self.tok = j['localId'], j['idToken']

    def _fs(self, method, path, body=None):
        url = FS + '/' + path
        r = urllib.request.Request(url, data=json.dumps(body).encode() if body else None, method=method,
            headers={'Content-Type':'application/json','Authorization':'Bearer '+self.tok,'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        try:
            with urllib.request.urlopen(r, timeout=30, context=CTX) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            raise RuntimeError('%s %s %s: %s' % (method, path, e.code, e.read(300)))

    def user(self):
        try:
            return self._fs('GET', 'users/%s' % self.uid).get('fields', {})
        except Exception:
            return {}

    def credits(self):
        return int(self.user().get('credit',{}).get('integerValue','0'))

    def enhance_prompt(self, prompt):
        try:
            req = urllib.request.Request('https://apis.dreamerland.ai/enhance-prompt',
                data=json.dumps({'prompt':prompt,'uid':self.uid}).encode(), method='POST',
                headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req, timeout=30, context=CTX) as r:
                return json.loads(r.read()).get('enhanced_prompt', prompt)
        except Exception:
            return prompt

    def submit(self, prompt, model='z_image_turbo', task='txt2img', ratio='square', steps=None, scale=None, neg=''):
        mtype, misc = MODELS.get(model, ('zimage', True))
        fields = {
          'version':{'stringValue':VERSION}, 'prompt':{'stringValue':prompt},
          'negPrompt':{'stringValue':neg}, 'task':{'stringValue':task},
          'aspectRatio':{'stringValue':ratio}, 'ratio':{'stringValue':ratio},
          'styles':{'arrayValue':{'values':[]}},
          'steps':{'integerValue':str(steps or (25 if mtype in ('krea2','flux2') else 50))},
          'scale':{'doubleValue': scale if scale is not None else (4 if mtype=='krea2' else 1)},
          'createdAt':{'integerValue':str(int(time.time()*1000))},
          'status':{'stringValue':'queueing'}, 'model':{'stringValue':model},
          'modelType':{'stringValue':mtype}, 'seed':{'integerValue':'0'},
          'img2img':{'booleanValue':False}, 'inpaint':{'booleanValue':False},
          'favourite':{'booleanValue':False}, 'hiresfix':{'booleanValue':False},
          'isVideo':{'booleanValue':False}, 'batch':{'integerValue':'1'},
          'web':{'booleanValue':True}, 'platform':{'stringValue':'web'},
          'folder':{'stringValue':''}, 'scheduler':{'stringValue':'euler'},
          'clipSkip':{'integerValue':'2'},
        }
        if misc: fields['misc'] = {'booleanValue': True}
        j = self._fs('POST', 'users/%s/jobs' % self.uid, {'fields':fields})
        return j['name'].rsplit('/',1)[-1]

    def status(self, jid):
        f = self._fs('GET', 'users/%s/jobs/%s' % (self.uid, jid))['fields']
        return f.get('status',{}).get('stringValue','?'), f

    def wait(self, jid, timeout=300):
        t0=time.time()
        while time.time()-t0 < timeout:
            st, f = self.status(jid)
            if st == 'completed':
                return [v['stringValue'] for v in f.get('images',{}).get('arrayValue',{}).get('values',[])]
            if st in ('ERROR','failed','error','cancelled'):
                raise RuntimeError('job %s: %s' % (jid, st))
            time.sleep(5)
        raise TimeoutError(jid)

    def generate(self, prompt, wait=True, **kw):
        jid = self.submit(prompt, **kw)
        if not wait: return jid
        return self.wait(jid)

if __name__ == '__main__':
    import sys
    c = DreamerlandClient()
    print('uid:', c.uid, 'credits:', c.credits())
    p = ' '.join(sys.argv[1:]) or 'a cat'
    eid = c.enhance_prompt(p)
    print('enhanced:', eid[:150])
    urls = c.generate(eid, model='z_image_turbo')
    print('IMAGES:', urls)
