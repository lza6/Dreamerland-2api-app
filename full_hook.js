// 全量 hook: 防自卸载 + Flutter SSL 明文抓包 + okhttp Java 层兜底
function hookFlutter(attempt) {
    var mods = Process.enumerateModules();
    var fl = null;
    for (var i = 0; i < mods.length; i++) if (mods[i].name.indexOf('libflutter.so') >= 0) { fl = mods[i]; break; }
    if (!fl) { if (attempt < 120) { setTimeout(function(){hookFlutter(attempt+1);}, 500); } else console.log('[-] no libflutter'); return; }
    console.log('[+] libflutter.so @ ' + fl.base);
    var syms = fl.enumerateSymbols();
    var wAddr=null, rAddr=null;
    for (var i=0;i<syms.length;i++){
        var n=syms[i].name;
        if (!wAddr && n.indexOf('ssl_write')>=0 && n.indexOf('ssl_log')<0) wAddr=syms[i].address;
        if (!rAddr && n.indexOf('ssl_read')>=0 && n.indexOf('ssl_log')<0) rAddr=syms[i].address;
    }
    console.log('[*] ssl_write=' + wAddr + ' ssl_read=' + rAddr);
    if (wAddr) Interceptor.attach(wAddr, {
        onEnter: function(a){ this.b=a[1]; this.l=a[2].toInt32(); },
        onLeave: function(r){ if(this.l>0){ try{
            var d=Memory.readByteArray(this.b, Math.min(this.l, 8000));
            var s = '';
            var u8 = new Uint8Array(d);
            for (var i=0;i<u8.length && i<6000;i++){ var c=u8[i]; s += (c>=32&&c<127)?String.fromCharCode(c):'.'; }
            if (s.indexOf('POST ')>=0||s.indexOf('GET ')>=0||s.indexOf('PUT ')>=0) console.log('\n######## REQ ########\n'+s);
        }catch(e){} } }
    });
    if (rAddr) Interceptor.attach(rAddr, {
        onEnter: function(a){ this.b=a[1]; },
        onLeave: function(r){ var l=r.toInt32(); if(l>0){ try{
            var u8 = new Uint8Array(Memory.readByteArray(this.b, Math.min(l, 8000)));
            var s='';
            for (var i=0;i<u8.length && i<6000;i++){ var c=u8[i]; s += (c>=32&&c<127)?String.fromCharCode(c):'.'; }
            if (s.indexOf('HTTP')>=0 || (s.indexOf('{')>=0 && s.indexOf('"')>=0)) console.log('\n######## RES ########\n'+s);
        }catch(e){} } }
    });
    console.log('[+] flutter ssl hooks done');
}

Java.perform(function(){
    try {
        var PM = Java.use('android.app.ApplicationPackageManager');
        PM.deletePackage.overload('java.lang.String','android.content.pm.IPackageDeleteObserver','int').implementation = function(p,o,f){ console.log('[!!] blocked deletePackage '+p); };
        console.log('[+] anti-deletePackage');
    } catch(e){ console.log('[-]pm '+e); }
});
setTimeout(function(){ hookFlutter(0); }, 300);
