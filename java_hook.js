// Java 层全量网络 hook (Flutter dart:io 在 Android 上仍走 Conscrypt/OpenSSL - 实际 dart:io 用内置 BoringSSL，但 okio/okhttp 与 firebase SDK 走 Java 层)
Java.perform(function () {
    // 1. Conscrypt / Platform TrustManager 不可拦 dart:io。改从 socket 输入流抓
    //    dart:io SecureSocket -> SSLSocket? 不, dart:io 用自己的. 但 Firebase/Auth/okhttp 全走 Java.
    var  OS = Java.use('java.io.OutputStream');
    // 2. okhttp3
    try {
        var RealCall = Java.use('okhttp3.internal.connection.RealCall');
        RealCall.getResponseWithInterceptorChain.implementation = function () {
            var req = this.request();
            var url = req.url().toString();
            var body = req.body();
            var bodyStr = '';
            if (body != null) {
                var buf = Java.use('okio.Buffer').$new();
                try { body.writeTo(buf); bodyStr = buf.readUtf8(); } catch (e) { bodyStr = '<binary ' + body.contentLength() + 'b>'; }
            }
            console.log('\n#### OKREQ ' + req.method() + ' ' + url + '\nHEADERS: ' + req.headers().toString() + '\nBODY: ' + bodyStr.substring(0, 3000));
            var resp = this.getResponseWithInterceptorChain();
            try {
                var peek = resp.peekBody(8000);
                console.log('\n#### OKRES ' + resp.code() + ' ' + url + '\n' + peek.string().substring(0, 3000));
            } catch (e) { console.log('#### OKRES ' + resp.code()); }
            return resp;
        };
        console.log('[+] okhttp hooked');
    } catch (e) { console.log('[-] okhttp ' + e); }
    // 3. 备用: SSLContext + HttpsURLConnection
    try {
        var URLConn = Java.use('javax.net.ssl.HttpsURLConnection');
        URLConn.getInputStream.implementation = function () {
            console.log('\n#### URLCONN GET ' + this.getURL().toString());
            return this.getInputStream();
        };
    } catch (e) {}
});
