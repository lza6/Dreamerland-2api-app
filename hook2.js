// 延迟等待 libflutter.so 加载后再 hook
function tryHook(attempt) {
    var flutter = null;
    var mods = Process.enumerateModules();
    for (var i = 0; i < mods.length; i++) if (mods[i].name.indexOf('libflutter.so') >= 0) { flutter = mods[i]; break; }
    if (!flutter) {
        if (attempt < 40) { setTimeout(function(){ tryHook(attempt+1); }, 500); return; }
        console.log('[-] libflutter.so never appeared'); return;
    }
    console.log('[+] libflutter.so found at ' + flutter.base);
    var count = 0, hooked = false;
    var syms = flutter.enumerateSymbols();
    console.log('[*] total symbols: ' + syms.length);
    for (var i = 0; i < syms.length; i++) {
        var n = syms[i].name;
        if ((n === 'ssl_write' || n.indexOf('ssl_write') >= 0) && count < 1) {
            Interceptor.attach(syms[i].address, {
                onEnter: function(args){ this.b=args[1]; this.l=args[2].toInt32(); },
                onLeave: function(r){
                    if(this.l>0){
                        try{ var d=Memory.readUtf8String(this.b, Math.min(this.l,4000));
                            if(d && (d.indexOf('POST ')>=0||d.indexOf('GET ')>=0)) console.log('\n==REQ==\n'+d.substring(0,3500));
                        }catch(e){}
                    }
                }
            });
            console.log('[+] hooked ssl_write @ ' + syms[i].address); hooked=true; break;
        }
    }
    for (var i = 0; i < syms.length; i++) {
        var n = syms[i].name;
        if (n === 'ssl_read' || n.indexOf('ssl_read') >= 0) {
            Interceptor.attach(syms[i].address, {
                onEnter: function(args){ this.b=args[1]; },
                onLeave: function(r){
                    var l=r.toInt32();
                    if(l>0){ try{ var d=Memory.readUtf8String(this.b, Math.min(l,4000));
                        if(d && (d.indexOf('{')>=0||d.indexOf('HTTP')>=0)) console.log('\n==RES==\n'+d.substring(0,3500));
                    }catch(e){} }
                }
            });
            console.log('[+] hooked ssl_read @ ' + syms[i].address); break;
        }
    }
    if(!hooked) console.log('[-] ssl_write not found in symbols');
}
setTimeout(function(){ tryHook(0); }, 300);
