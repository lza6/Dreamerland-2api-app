// Dreamerland Flutter 网络全量 hook — 抓 HTTPS 明文（BoringSSL SSL_write/SSL_read）
// Flutter 的 dart:io 走 BoringSSL (libflutter.so 内静态链接), 拦 ssl_crypto_x509 或直接 SSL_read/SSL_write
function hookFlutterSSL() {
    var mods = Process.enumerateModules();
    var flutter = null;
    for (var i = 0; i < mods.length; i++) if (mods[i].name.indexOf('libflutter.so') >= 0) { flutter = mods[i]; break; }
    if (!flutter) { console.log('[-] libflutter.so not found'); return; }
    console.log('[+] libflutter.so base=' + flutter.base + ' size=' + flutter.size);

    // 方法1: 找 ssl_write / SSL_write 符号 (release flutter 去符号, 按特征扫描 "ssl_write" 字符串引用太复杂)
    // 用通用法: 拦 BoringSSL 的 SSL_read/SSL_write — 通过扫描导出表失败时按模式
    var symbols = flutter.enumerateSymbols();
    var targets = {};
    for (var i = 0; i < symbols.length; i++) {
        var n = symbols[i].name;
        if (n.indexOf('SSL_write') >= 0 && n.indexOf('ssl') >= 0) targets['SSL_write'] = symbols[i];
        if (n.indexOf('SSL_read') >= 0 && n.indexOf('ssl') >= 0) targets['SSL_read'] = symbols[i];
    }
    console.log('[*] ssl symbols: ' + JSON.stringify(Object.keys(targets)));
    if (!targets['SSL_write'] || !targets['SSL_read']) {
        // fallback: dart:io 在 Flutter 里其实走 socket -> 加密前是 _SecureFilterImpl
        console.log('[*] falling back to Java layer okhttp/dio hooks');
        return false;
    }
    var SSL_write = targets['SSL_write'].address;
    var SSL_read = targets['SSL_read'].address;

    Interceptor.attach(SSL_write, {
        onEnter: function (args) { this.buf = args[1]; this.len = args[2].toInt32(); },
        onLeave: function (r) {
            if (this.len > 0 && this.len < 65536) {
                try {
                    var data = Memory.readUtf8String(this.buf, Math.min(this.len, 4096));
                    if (data && data.indexOf('HTTP') >= 0 || (data && data.indexOf('{') >= 0)) {
                        console.log('\n=====> SSL_write (' + this.len + '):\n' + data.substring(0, 3000));
                    }
                } catch (e) {}
            }
        }
    });
    Interceptor.attach(SSL_read, {
        onEnter: function (args) { this.buf = args[1]; },
        onLeave: function (r) {
            var n = r.toInt32();
            if (n > 0 && n < 65536) {
                try {
                    var data = Memory.readUtf8String(this.buf, Math.min(n, 4096));
                    if (data && (data.indexOf('{') >= 0 || data.indexOf('HTTP') >= 0)) {
                        console.log('\n<===== SSL_read (' + n + '):\n' + data.substring(0, 3000));
                    }
                } catch (e) {}
            }
        }
    });
    console.log('[+] SSL hooks installed');
    return true;
}

setImmediate(function () {
    hookFlutterSSL();
});
