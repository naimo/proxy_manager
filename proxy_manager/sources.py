import requests

class ProxySource():
    @classmethod
    def fetch(cls):
        r = requests.get(cls.URL)
        return r.text.strip().splitlines()

class ClarketmSource(ProxySource):
    URL = "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt"

class A2uSource(ProxySource):
    URL = "https://raw.githubusercontent.com/a2u/free-proxy-list/master/free-proxy-list.txt"

class TheSpeedXSource(ProxySource):
    URL = "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt"

if __name__ == "__main__":
    print(TheSpeedXSource.fetch())