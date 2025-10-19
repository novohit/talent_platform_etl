import requests

targetURL = "https://test.ipw.cn"
proxyAddr = "overseas-hk.tunnel.qg.net:17710"
authKey = "TYU1WZG9"
password = "C3BBFDA6FCE7"

proxyUrl = "http://%(user)s:%(password)s@%(server)s" % {
    "user": authKey,
    "password": password,
    "server": proxyAddr,
}

proxies = {
    "http": proxyUrl,
    "https": proxyUrl,
}

resp = requests.get(targetURL, proxies=proxies)
print(resp.text)
