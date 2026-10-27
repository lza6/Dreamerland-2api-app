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
