// DNS 解析 hook: 抓所有 app 请求的域名（Mod 壳 + Dreamerland 全量）
Java.perform(function () {
    var InetAddress = Java.use('java.net.InetAddress');
    InetAddress.getAllByName.overload('java.lang.String').implementation = function (host) {
        console.log('[DNS] ' + host);
        return this.getAllByName(host);
    };
    console.log('[+] DNS hook ok');
});
