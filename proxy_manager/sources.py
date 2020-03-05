import aiohttp
import re

IP_PORT_PATTERN = re.compile("((?:[0-9]{1,3}\.){3}[0-9]{1,3}):([0-9]+)")

class ProxySource():
    @classmethod
    async def fetch(cls):
        hosts_ports = set()
        async with aiohttp.ClientSession() as session:
            async with session.get(cls.URL) as r:
                text = await r.text()
                for line in re.split('(?:<br>)|\n|\r', text):
                    m = IP_PORT_PATTERN.search(line)
                    if m is not None:
                        hosts_ports.add(m.groups())
        return hosts_ports

class ClarketmSource(ProxySource):
    URL = "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt"

class A2uSource(ProxySource):
    URL = "https://raw.githubusercontent.com/a2u/free-proxy-list/master/free-proxy-list.txt"

class TheSpeedXSource(ProxySource):
    URL = "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt"

class HttpTunnelGe(ProxySource):
    URL = "http://www.httptunnel.ge/ProxyListForFree.aspx"

class ProxyTimeRu(ProxySource):
    URL = "http://proxytime.ru/http"

class GatherProxyCom(ProxySource):
    URL = "http://www.gatherproxy.com"

if __name__ == "__main__":
    print(GatherProxyCom.fetch())
