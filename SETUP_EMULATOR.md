# Dreamerland Mod 动态环境备忘 (fs16 + client 16.5.9)

## 关键版本锁定
- frida-server 必须用 /data/local/tmp/fs16 (16.5.9) — fs17(17.24.3) 的 Java bridge 在此模拟器上不可用(Java is not defined)
- 宿主端: pip install frida==16.5.9 frida-tools~=13.0

## 启动序列
adb -s emulator-5554 shell "su 0 sh -c 'pkill -f fs17; pkill -f fs16'" 
adb -s emulator-5554 shell "su 0 sh -c '/data/local/tmp/fs16 &'"
adb install -r D:/dreamerland-2api-app/dreamerland.apk   # 壳会自卸载, 每轮重装
adb shell am start -n art.dreamerai.android/.MainActivity
python inject_persist.py <pid>          # attach 后 antikill+appcheck+SSL hook 生效

## UI 流程坐标 (1080x2340)
1. Mod壳协议弹窗"同意" = (538,1510)
2. 登录页条款勾选 = (95,2055)
3. "Continue as a guest" = (538,1791)
4. 权限弹窗 Allow = (538,1325)
5. onboarding Continue = (538,2130)
6. 更新弹窗 Ignore = (315,1835)

## 已知坑
- 壳自卸载: antikill 只挡 Java 层 PM.deletePackage/Runtime.exec; 壳还有 native 路径, 进程死后包消失 → 重装
- Flutter 引擎以匿名 anon r-x 映射加载(无 libflutter.so 名), hook_flutter_net.js 找不到模块 → 需内存特征码扫描 (73 73 6c 5f 73 74 61 74 65 5f 6d 61 63 68 69 6e 65 = "ssl_state_machine")
- FirebaseAppCheck.getAppCheckToken 有多个 overload, hook 时需遍历 overloads 而非指定 boolean
- 模拟器 adb 偶发 offline(qemu重启), 等 sys.boot_completed=1
- 多设备时 ANDROID_SERIAL=emulator-5554 或 adb -s
