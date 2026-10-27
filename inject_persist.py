# -*- coding: utf-8 -*-
# 持久注入: python frida API, attach 后保活并实时写日志
import frida, sys, time

LOG = open(r'D:\dreamerland-2api-app\capture.log', 'w', encoding='utf-8', buffering=1)
def on_message(msg, data):
    if msg['type'] == 'send':
        LOG.write(msg['payload'] + '\n')
    elif msg['type'] == 'error':
        LOG.write('[JS-ERR] ' + msg.get('stack','')[:300] + '\n')

SCRIPT = open(r'D:\dreamerland-2api-app\hook_full.js', encoding='utf-8').read()
# 把 console.log 转成 send 以便 python 落盘
SCRIPT = SCRIPT.replace('console.log(', 'send(')

dev = frida.get_usb_device(timeout=15)
# attach with retry
pid = int(sys.argv[1])
for attempt in range(3):
    try:
        session = dev.attach(pid)
        break
    except Exception as e:
        print('attach fail', e); time.sleep(2)
script = session.create_script(SCRIPT, runtime='v8')
script.on('message', on_message)
script.load()
print('loaded, capturing...')
LOG.write('=== session start pid=%d ===\n' % pid)
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass
