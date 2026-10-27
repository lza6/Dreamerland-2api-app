# -*- coding: utf-8 -*-
import frida, time, subprocess, sys

ADB = ['adb','-s','emulator-5554']
def sh(*args): return subprocess.run(ADB+list(args),capture_output=True,text=True).stdout.strip()

out = open(r'D:\dreamerland-2api-app\capture.log','w',encoding='utf-8',buffering=1)
def on_msg(m,d):
    if m['type']=='send': out.write(m['payload']+'\n')
    elif m['type']=='error': out.write('[JS-ERR] '+m.get('description','')[:200]+'\n')

dev = frida.get_usb_device(timeout=15)
pid = dev.spawn(['art.dreamerai.android'])
session = dev.attach(pid)
js = open(r'D:\dreamerland-2api-app\hook_full.js',encoding='utf-8').read().replace('console.log(','send(')
script = session.create_script(js)
script.on('message', on_msg)
script.load()
dev.resume(pid)
out.write(f'=== spawned+hooked pid={pid} ===\n')
print('spawned+hooked', pid)
time.sleep(8)

# UI flow
import subprocess
def tap(x,y,sleep=2):
    sh('shell','input','tap',str(x),str(y)); time.sleep(sleep)

# Mod协议弹窗 (若有)
tap(538,1510,3)
# 登录页: 勾条款
tap(95,2055,1)
# guest
tap(538,1791,5)
# 可能再弹协议
tap(538,1510,8)
# 权限 Allow
tap(538,1325,3)
out.write('=== UI flow done, waiting network ===\n')
print('flow done')

# 保持会话 5 分钟观察
for i in range(30):
    time.sleep(10)
    r = sh('shell','pidof','art.dreamerai.android')
    if r != str(pid):
        out.write(f'!!! process died at t+{(i+1)*10}s (now={r!r})\n')
        print('DIED at', (i+1)*10)
        break
else:
    out.write('=== survived 5min ===\n')
    print('SURVIVED')
