# -*- coding: utf-8 -*-
import frida, time, subprocess
ADB=['adb','-s','emulator-5554']
def sh(*a): return subprocess.run(ADB+list(a),capture_output=True,text=True).stdout.strip()
out=open(r'D:\dreamerland-2api-app\capture.log','w',encoding='utf-8',buffering=1)
def on_msg(m,d):
    if m['type']=='send': out.write(m['payload']+'\n')
    elif m['type']=='error': out.write('[JS-ERR] '+m.get('description','')[:200]+'\n')
dev=frida.get_usb_device(timeout=15)
pid=dev.spawn(['art.dreamerai.android'])
session=dev.attach(pid)
js=open(r'D:\dreamerland-2api-app\hook_full.js',encoding='utf-8').read().replace('console.log(','send(')
script=session.create_script(js); script.on('message',on_msg); script.load()
dev.resume(pid); out.write(f'=== hooked pid={pid} ===\n'); print('hooked',pid)
time.sleep(6)
def tap(x,y,s=2): sh('shell','input','tap',str(x),str(y)); time.sleep(s)
tap(538,1510,3); tap(95,2055,1); tap(538,1791,5); tap(538,1510,8); tap(538,1325,3)
out.write('=== flow done ===\n'); print('flow done')
alive=0
for i in range(40):
    time.sleep(10)
    r=sh('shell','pidof','art.dreamerai.android')
    if r==str(pid): alive+=1
    else:
        out.write(f'died t+{(i+1)*10}s\n'); print('DIED'); break
else:
    out.write(f'=== survived, {alive} checks ===\n'); print('SURVIVED',alive)
