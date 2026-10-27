// 阻止 Dreamerland mod 壳自卸载: hook PackageManager.deletePackage / 锁屏级自毁
Java.perform(function () {
    try {
        var PM = Java.use('android.app.ApplicationPackageManager');
        // deletePackage(uid observer flags)
        PM.deletePackage.overload('java.lang.String','android.content.pm.IPackageDeleteObserver','int')
            .implementation = function (pkg, obs, flags) {
                console.log('[!!] BLOCKED deletePackage: ' + pkg);
                return;
            };
        console.log('[+] deletePackage hooked');
    } catch (e) { console.log('[-] PM ' + e); }
    // 覆盖 runtime exec rm 命令
    try {
        var RT = Java.use('java.lang.Runtime');
        RT.exec.overload('java.lang.String').implementation = function (cmd) {
            console.log('[exec] ' + cmd);
            if (cmd.indexOf('pm uninstall') >= 0 || cmd.indexOf('delete') >= 0) {
                console.log('[!!] blocked: ' + cmd);
                return Java.use('java.lang.ProcessBuilder').construct(['true']).start();
            }
            return this.exec(cmd);
        };
        console.log('[+] Runtime.exec hooked');
    } catch (e) { console.log('[-] RT ' + e); }
    // ProcessBuilder
    try {
        var PB = Java.use('java.lang.ProcessBuilder');
        PB.start.implementation = function () {
            var cmd = this.command().toString();
            console.log('[pb] ' + cmd);
            if (cmd.indexOf('uninstall') >= 0) {
                console.log('[!!] blocked pb');
                return Java.use('java.lang.ProcessBuilder').construct(['true']).start();
            }
            return this.start();
        };
        console.log('[+] ProcessBuilder hooked');
    } catch (e) { console.log('[-] PB ' + e); }
});
// Dreamerland App Check 绕过 + Firebase Auth/网络全量抓取
// hook: getAppCheckToken (Java层 firebase.appcheck) + BoringSSL SSL_write/read (Flutter网络)
Java.perform(function () {
    // 1) Java 层: firebase AppCheck token 拦截
    try {
        var FAC = Java.use('com.google.firebase.appcheck.debug.DebugAppCheckProviderFactory');
        console.log('[+] has DebugAppCheckProvider');
    } catch(e) {}
    try {
        var IAC = Java.use('com.google.firebase.appcheck.internal.DefaultFirebaseAppCheck');
        IAC.getAppCheckToken.overload('boolean').implementation = function(force) {
            var r = this.getAppCheckToken(force);
            try { console.log('[APPCHECK] ' + r.getToken()); } catch(e){ console.log('[APPCHECK] obj=' + r); }
            return r;
        };
        console.log('[+] DefaultFirebaseAppCheck hooked');
    } catch(e) { console.log('[-] DefaultFirebaseAppCheck: ' + e.message); }
    try {
        // 一般入口: FirebaseAppCheck.getInstance().getAppCheckToken()
        var FBAC = Java.use('com.google.firebase.appcheck.FirebaseAppCheck');
        FBAC.getAppCheckToken.overload().implementation = function() {
            var r = this.getAppCheckToken();
            try { console.log('[APPCHECK-pub] ' + r.getToken()); } catch(e){ console.log('[APPCHECK-pub] ' + r); }
            return r;
        };
        console.log('[+] FirebaseAppCheck public hooked');
    } catch(e) { console.log('[-] FirebaseAppCheck: ' + e.message); }

    // 2) okhttp Request dump (可能有 Java 层网络)
    try {
        var OB = Java.use('okhttp3.Request$Builder');
        var methods = OB.class.getDeclaredMethods();
        // skip heavy: just log url on build
    } catch(e) {}
});
// 3) Flutter BoringSSL
function hookFlutter() {
    var flutter = Process.findModuleByName('libflutter.so');
    if (!flutter) { setTimeout(hookFlutter, 1000); return; }
    console.log('[+] libflutter.so ' + flutter.base);
    var syms = flutter.enumerateSymbols();
    var w=null, r=null;
    for (var i=0;i<syms.length;i++){
        var n = syms[i].name;
        if (!w && n.indexOf('SSL_write')>=0) w = syms[i];
        if (!r && n.indexOf('SSL_read')>=0) r = syms[i];
    }
    if (!w || !r) { console.log('[-] no SSL symbols (release stripped)'); return; }
    console.log('[+] SSL_write @ ' + w.address);
    Interceptor.attach(w.address, {
        onEnter: function(a){ this.b=a[1]; this.l=a[2].toInt32(); },
        onLeave: function(ret){
            if (this.l<=0 || this.l>200000) return;
            try {
                var s = Memory.readUtf8String(this.b, Math.min(this.l, 4000));
                if (s && (s.indexOf('firestore')>=0 || s.indexOf('appcheck')>=0 || s.indexOf('dreamerland')>=0 || s.indexOf('identitytoolkit')>=0 || s.indexOf('Bearer')>=0))
                    console.log('>>>SSL_WRITE ' + this.l + '\n' + s.substring(0,3500) + '\n<<<');
            } catch(e){}
        }
    });
    Interceptor.attach(r.address, {
        onEnter: function(a){ this.b=a[1]; this.l=a[2].toInt32(); },
        onLeave: function(ret){
            var n = ret.toInt32(); if (n<=0 || n>200000) return;
            try {
                var s = Memory.readUtf8String(this.b, Math.min(n, 4000));
                if (s && (s.indexOf('appcheck')>=0 || s.indexOf('firestore')>=0 || s.indexOf('token')>=0))
                    console.log('<<<SSL_READ ' + n + '\n' + s.substring(0,2500) + '\n===');
            } catch(e){}
        }
    });
    console.log('[+] SSL hooks active — 现在操作App触发请求');
}
setTimeout(hookFlutter, 500);
