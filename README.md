# Dreamerland 1.60.0 逆向 — 协议提取 + 2API 全链路实现

> APK: Telegram 流通破解版 (RollingHunters mod, `MODDED+BY+ROLLING+HUNTERS`, 频道 t.me/+oBYmjb5Jv64xZjU1)
> 目标 App: `art.dreamerai.android` (Flutter) — AI 生图/视频聚合平台

## 🎯 最终成果

**完全打通生成链路**：Firebase 匿名注册 → Firestore 任务提交 → worker 真实生成 → 图片 URL。两张实测真图：
- `generated_cat.webp` (z_image_turbo, 71KB)
- `generated_city.webp` (z_image_turbo, 184KB)

生产级 Python 客户端：`dreamerland_api.py`
```python
from dreamerland_api import DreamerlandClient
c = DreamerlandClient()          # 自动注册/复用账号+token刷新
c.enhance_prompt('a cat')        # LLM 提词增强 (apis.dreamerland.ai)
urls = c.generate('a cat', model='z_image_turbo', wait=True)
c.credits()                      # 余额查询 (匿名送 8 credits, 每图扣 4)
```

## 🏗️ 架构全貌

```
App (Flutter, art.dreamerai.android)
 ├── Firebase Auth (项目 dreamer-ai) — 匿名/Google/FB 登录
 │    apiKey: AIzaSyBbdlG-RVEOmY84ch5sxgNeXGV8ZpzaQNQ (有效)
 │            AIzaSyCoLUy12KbmxMuOHVHT2zR8p6-r6It6low (identitytoolkit被block)
 │            AIzaSyCvXZ4XQl0d6Z52HdXqeBeNwHWmS6fyoIo
 ├── Firestore (dreamer-ai) — 用户/任务/历史
 │    users/{uid}                    余额/设置 (匿名送 credit=8, freeVideoQuota=3, inpaintFreeTrial=10)
 │    users/{uid}/jobs/{jobId}       ★ 生成任务队列 (status: queueing→processing→completed/ERROR)
 ├── FastAPI 网关 apis.dreamerland.ai (46 路径, /openapi.json 公开)
 │    /enhance-prompt /generate-image-prompt /text-to-speech /check_kling_image
 │    /styles /style /list/history/{uid} /upload/image /import_civitai_lora ...
 │    /{fal,piapi,runpod,kie,seedance}_webhook/{uid}/{jid}  ← worker 回调
 ├── Cloud Functions us-central1-dreamer-ai (uploadImage 等)
 └── CDN static{,2,4,6}.dreamerland.ai / static.dreamerai.art
 上游供应商 (由 webhook 路径推断): fal.ai / PiAPI / RunPod / KIE / Seedance
 计费: Stripe (credits 订阅) + RevenueCat
```

## 🔑 生成协议 (核心机密 — users/{uid}/jobs 文档)

提交 = `POST https://firestore.googleapis.com/v1/projects/dreamer-ai/databases/(default)/documents/users/{uid}/jobs`
Bearer = Firebase idToken（匿名注册即得）。字段：

| 字段 | 值 (txt2img 最小可用集) |
|---|---|
| version | "1.40.0" (web bundle 常量) |
| prompt / negPrompt | 文本 / "" |
| task | "txt2img" |
| aspectRatio + ratio | "square" (或 portrait/landscape/portrait_hd/landscape_hd/instagram) |
| styles | [] |
| steps | 50 (zimage) / 25 (krea2, flux2) |
| scale | 1 (krea2=4) |
| scheduler | "euler" |
| clipSkip | 2 |
| **status** | **"queueing"** ← 不是 pending! worker 靠它拾取 |
| model | "z_image_turbo" 等 (见下模型库) |
| modelType | zimage/flux2/nano_banana/seedream/gpt_image/krea2/anima |
| seed | 0 (随机) |
| img2img/inpaint/favourite/hiresfix/isVideo | false |
| batch | 1 |
| web / platform / folder / misc | true / "web" / "" / true |

完成后回写: `images[]`(static6 URL), `nsfw[]`, `seed`, `queueName`("pro-jobs-3"), `host/hostname`, `completedAt`, status="completed"

### 模型库 (web bundle + AOT 快照提取, 90+)
zimage: z_image_turbo, z_image_moody_mix · flux2: flux2_klein · nano_banana: nano_banana, _2, _pro (premium)
seedream: seedream45, seedream50lite, seedream50pro (premium) · gpt_image: gpt_image_2, _25 (premium)
krea2: krea2_turbo · anima: anima_official 等 · plus: illustrious/pony/sdxl 全家桶 (170+ 社区LoRA)
视频: wan2.2, kling, hunyuan, seedance (1.65.0 将加 Seedance 2.5 / MiniMax H3)

## 🧪 实测记录
| 步骤 | 结果 |
|---|---|
| Firebase 匿名注册 (key2) | ✅ 200, uid+idToken |
| enhance-prompt (真实 uid) | ✅ 返回 LLM 增强文本 |
| Firestore 读 users/{uid} | ✅ credit=8 |
| Firestore 写 jobs | ✅ 200 (规则允许自建) |
| worker 生成 (z_image_turbo) | ✅ ~15s 完成, 真图 71KB/184KB |
| 每图扣费 | 4 credits |

## ⚠️ 坑
1. FS 常量结尾**必须有 `/`** — 否则 Google 返回 HTML 404 页（不是 JSON），排查了一小时
2. Firestore 权限: 读自己 user/jobs ✅，listCollectionIds/跨用户 ❌
3. enhance-prompt 对「无 user 文档的新号」403
4. idToken 1h 过期 → securetoken.googleapis.com/v1/token 刷新
5. 模拟器动态分析: mod 壳反复自卸载(触发器未明)，Flutter ARM 翻译模式下 libflutter 无法符号 hook — 静态 web bundle (gallery.dreamerland.ai) 反而是最优协议来源
6. status 必须是 `queueing`；写 `pending` worker 不理 (ERROR)

## 📁 文件
- `dreamerland_api.py` — 生产级客户端库 ★
- `submit_job.py` / `poll_job.py` / `read_job.py` — 协议验证脚本
- `auth_test.py` — Firebase 注册验证
- `demo/demo_server.py` + `demo.html` — mock 演示(第一轮)
- `hook_*.js` — frida 脚本 (anti-kill/DNS/Java 层)
- `gallery_main.js` — 官网 web bundle (协议金矿)
- `sources-key-files/` — 关键证据
