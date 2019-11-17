import requests

class ProxySource():
    @classmethod
    def fetch(cls):
        r = requests.get(cls.URL)
        return r.text.strip()

class ClarketmSource(ProxySource):
    URL = "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt"

if __name__ == "__main__":
    print(ClarketmSource.fetch())