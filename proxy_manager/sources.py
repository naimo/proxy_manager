import requests
import re

IP_PORT_PATTERN = re.compile("((?:[0-9]{1,3}\.){3}[0-9]{1,3}):([0-9]+)")

class ProxySource():
    @classmethod
    def fetch(cls):
        r = requests.get(cls.URL)
        hosts_ports = []
        for line in r.text.strip().splitlines():
            m = IP_PORT_PATTERN.search(line)
            if m is not None:
                hosts_ports.append(m.groups())
        return hosts_ports

class ClarketmSource(ProxySource):
    URL = "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt"

class A2uSource(ProxySource):
    URL = "https://raw.githubusercontent.com/a2u/free-proxy-list/master/free-proxy-list.txt"

class TheSpeedXSource(ProxySource):
    URL = "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt"

if __name__ == "__main__":
    print(TheSpeedXSource.fetch())