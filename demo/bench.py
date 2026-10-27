# -*- coding: utf-8 -*-
"""本地压测：只打 127.0.0.1:8791 mock，不碰真实上游"""
import json, time, threading, statistics, urllib.request

BASE='http://127.0.0.1:8791'
def call(path, body=None):
    d = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE+path, data=d, method='POST' if d else 'GET',
        headers={'Content-Type':'application/json'})
    t0=time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            r.read(); return r.status, (time.perf_counter()-t0)*1000
    except urllib.error.HTTPError as e:
        e.read(); return e.code, (time.perf_counter()-t0)*1000

def bench(name, path, body, n=200, c=10):
    lat=[]; codes={}; lock=threading.Lock()
    def worker():
        while True:
            with lock:
                if len(lat)>=n: return
            s,ms=call(path,body)
            with lock:
                lat.append(ms); codes[s]=codes.get(s,0)+1
    t0=time.perf_counter()
    ths=[threading.Thread(target=worker) for _ in range(c)]
    [t.start() for t in ths]; [t.join() for t in ths]
    dur=time.perf_counter()-t0
    lat.sort()
    p50=lat[len(lat)//2]; p99=lat[int(len(lat)*0.99)-1]
    print(f"{name}: {n}req/{c}并发  rps={n/dur:.1f}  p50={p50:.1f}ms  p99={p99:.1f}ms  codes={codes}")

bench("健康检查 GET /health", "/health", None, n=200, c=10)
bench("模型列表 GET /v1/models", "/v1/models", None, n=200, c=10)
bench("生图 POST /v1/images/generations(并发10)", "/v1/images/generations", {"model":"dreamerland/flux","prompt":"bench test cat","n":1}, n=200, c=10)
bench("生图 POST /v1/images/generations(并发60)", "/v1/images/generations", {"model":"dreamerland/flux","prompt":"bench test cat","n":1}, n=200, c=60)
# 错误路径
bench("错误路径 空prompt(期望400)", "/v1/images/generations", {"model":"dreamerland/flux","prompt":""}, n=100, c=10)
