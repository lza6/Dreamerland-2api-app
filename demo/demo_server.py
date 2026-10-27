# -*- coding: utf-8 -*-
"""Dreamerland 2API demo server — OpenAI 兼容镜像 apis.dreamerland.ai 协议（本地 mock，无真实上游调用）"""
import json, time, uuid, random, threading, hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

PORT = 8791
MODELS = [
    {"id": "dreamerland/flux2-klein", "desc": "FLUX.2 Klein"},
    {"id": "dreamerland/flux", "desc": "FLUX.1"},
    {"id": "dreamerland/qwen-image", "desc": "Qwen-Image"},
    {"id": "dreamerland/qwen-image-edit", "desc": "Qwen-Image-Edit"},
    {"id": "dreamerland/nano-banana", "desc": "Nano Banana"},
    {"id": "dreamerland/nano-banana-pro", "desc": "Nano Banana Pro"},
    {"id": "dreamerland/seedream", "desc": "Seedream"},
    {"id": "dreamerland/hidream", "desc": "HiDream"},
    {"id": "dreamerland/illustrious-xl", "desc": "Illustrious XL (社区LoRA 170+)"},
    {"id": "dreamerland/pony-realism", "desc": "Pony Realism"},
    {"id": "dreamerland/wan2.2", "desc": "Wan 2.2 视频"},
    {"id": "dreamerland/kling", "desc": "Kling 视频"},
    {"id": "dreamerland/hunyuan-video", "desc": "Hunyuan 视频"},
    {"id": "dreamerland/z-image-turbo", "desc": "Z-Image Turbo"},
]
# 模拟任务池（模仿上游 webhook 任务队列模型）
_tasks = {}
_lock = threading.Lock()

def _fake_image(prompt):
    """生成一张小的确定性 PNG (1x1 灰度底图变体)"""
    # 最小 PNG: 签名+IHDR+IDAT+IEND, 8x8 纯色
    import struct, zlib
    w = h = 8
    seed = int(hashlib.md5(prompt.encode()).hexdigest()[:8], 16)
    raw = b''
    for y in range(h):
        raw += b'\x00' + bytes([(seed >> ((x*3+y) % 24)) & 0xFF for x in range(w*3)])
    def chunk(t, d):
        c = t + d
        return struct.pack('>I', len(d)) + c + struct.pack('>I', zlib.crc32(c))
    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(raw))
    png += chunk(b'IEND', b'')
    return png

class H(BaseHTTPRequestHandler):
    server_version = "Dreamerland2API/0.1"
    def log_message(self, fmt, *a):
        print("[%s] %s" % (time.strftime('%H:%M:%S'), fmt % a))

    def _json(self, code, obj):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def _body(self):
        n = int(self.headers.get('Content-Length') or 0)
        if not n: return {}
        try: return json.loads(self.rfile.read(n))
        except Exception: return {}

    def do_GET(self):
        u = urlparse(self.path); q = parse_qs(u.query)
        if u.path in ('/health', '/v1/health'):
            with _lock: n = len(_tasks)
            return self._json(200, {"status": "ok", "mode": "mock", "tasks": n,
                                    "upstream": "apis.dreamerland.ai (未直连)"})
        if u.path == '/v1/models':
            return self._json(200, {"object": "list", "data": [
                {"id": m["id"], "object": "model", "owned_by": "dreamerland"} for m in MODELS]})
        if u.path == '/v1/dreamerland/styles':
            return self._json(200, [{"_id": "mock1", "styleName": "Bruce Timm", "type": "lora",
                "triggerPrompt": "Bruce Timm, ", "styleWeight": 0.6, "category": "artists"}])
        if u.path.startswith('/v1/dreamerland/tasks/'):
            tid = u.path.rsplit('/', 1)[-1]
            with _lock: t = _tasks.get(tid)
            if not t: return self._json(404, {"error": "task not found"})
            t['status'] = 'succeeded' if time.time() > t['ready_at'] else 'processing'
            return self._json(200, t)
        return self._json(404, {"error": "not found"})

    def do_POST(self):
        u = urlparse(self.path)
        if u.path in ('/v1/images/generations', '/v1/images/edits'):
            b = self._body()
            prompt = b.get('prompt') or ''
            if not prompt:
                return self._json(400, {"error": {"message": "prompt is required", "type": "invalid_request_error"}})
            model = b.get('model', 'dreamerland/flux')
            n = min(max(int(b.get('n') or 1), 1), 4)
            uid = b.get('user', 'demo-uid')
            tid = uuid.uuid4().hex
            with _lock:
                _tasks[tid] = {"task_id": tid, "status": "processing", "model": model,
                               "prompt": prompt, "uid": uid, "ready_at": time.time() + 0.8,
                               "created": int(time.time())}
            imgs = [{"url": "data:image/png;base64,MOCK_%s_%d" % (tid[:12], i)} for i in range(n)]
            # 模拟上游: 提交后 0.8s ready; demo 直接同步返回 base64 占位
            return self._json(200, {"created": int(time.time()), "task_id": tid, "data": imgs,
                                    "upstream_note": "mock — 真实上游为 Firestore 任务队列 + webhook"})
        if u.path == '/v1/dreamerland/enhance-prompt':
            b = self._body()
            if not b.get('prompt'): return self._json(400, {"message": "prompt required", "status": "error"})
            if not b.get('uid'): return self._json(200, {"message": "User not found", "status": "error"})
            return self._json(200, {"status": "success",
                "enhanced": b['prompt'] + ", highly detailed, best quality, vivid colors, professional lighting"})
        if u.path == '/v1/audio/speech':
            b = self._body()
            if not b.get('text'): return self._json(400, {"error": "text required"})
            return self._json(200, {"audio_url": "mock://tts/" + uuid.uuid4().hex,
                                    "model": b.get('model', 'zonos-v0.1-transformer')})
        return self._json(404, {"error": "not found"})

if __name__ == '__main__':
    print("Dreamerland 2API demo (MOCK) listening on :%d" % PORT)
    ThreadingHTTPServer(('127.0.0.1', PORT), H).serve_forever()
