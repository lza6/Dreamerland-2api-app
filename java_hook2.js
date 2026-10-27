// 通用 Java 网络捕获: 枚举 classloader 找 okhttp, 不存在则兜底 URL/Stream hook
Java.perform(function () {
    var found = false;
    Java.enumerateClassLoaders({
        onMatch: function (loader) {
            if (found) return;
            try {
                var factory = Java.ClassFactory.get(loader);
                var RealCall = factory.use('okhttp3.internal.connection.RealCall');
                RealCall.getResponseWithInterceptorChain.implementation = function () {
                    var req = this.request();
                    var url = req.url().toString();
                    var body = req.body(); var bodyStr = '';
                    if (body != null) {
                        var buf = Java.use('okio.Buffer').$new();
                        try { body.writeTo(buf); bodyStr = buf.readUtf8(); } catch (e) { bodyStr = '<binary>'; }
                    }
                    console.log('\n#### OKREQ ' + req.method() + ' ' + url + ' H=' + req.headers().toString() + ' BODY=' + bodyStr.substring(0, 2500));
                    var resp = this.getResponseWithInterceptorChain();
                    try { console.log('\n#### OKRES ' + resp.code() + ' ' + url + ' ' + resp.peekBody(6000).string().substring(0, 2500)); } catch (e) {}
                    return resp;
                };
                console.log('[+] okhttp hooked via custom classloader');
                found = true;
            } catch (e) {}
        },
        onComplete: function () { if (!found) console.log('[-] okhttp3 not found in any classloader'); }
    });
    // 兜底: java.net.URL openConnection
    try {
        var URL = Java.use('java.net.URL');
        URL.openConnection.overload().implementation = function () {
            console.log('\n#### URL open: ' + this.toString());
            return this.openConnection();
        };
        console.log('[+] java.net.URL hooked');
    } catch (e) { console.log('[-]url ' + e); }
});
