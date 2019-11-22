import requests
import re

IP_PORT_PATTERN = re.compile("((?:[0-9]{1,3}\.){3}[0-9]{1,3}):([0-9]+)")

class ProxySource():
    @classmethod
    def fetch(cls):
        r = requests.get(cls.URL)
        hosts_ports = set()
        for line in re.split('(?:<br>)|\n|\r', r.text):
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

if __name__ == "__main__":
    print(len(ClarketmSource.fetch()))
    print(len(A2uSource.fetch()))
    print(len(TheSpeedXSource.fetch()))
    print(len(HttpTunnelGe.fetch()))
    print(len(ProxyTimeRu.fetch()))
