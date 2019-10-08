import random
import requests

class ProxyManager(object):
    def __init__(self, proxy_list):
        self.proxies = [Proxy(h,p) for (h,p) in [p.split(':') for p in proxy_list]]

    @classmethod
    def from_file(cls, filename):
        with open(filename) as f:
            content = f.readlines()
        # you may also want to remove whitespace characters like `\n` at the end of each line
        content = [x.strip() for x in content]       
        return cls(content)  

    def get_random_proxy(self):
        return random.choice(self.proxies)

    def remove_bad_proxy(self, proxy):
        self.proxies.remove(proxy)

    def to_file(self, filename):
        with open(filename, 'w') as f:
            f.write('\n'.join([str(p) for p in self.proxies]))

class Proxy(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def __eq__(self, other):
        if isinstance(other, Proxy):
            return (self.host == other.host) and (self.port == other.port)
        return False

    def __repr__(self):
        return self.get_url()

    def get_url(self):
        return self.host+":"+str(self.port)

    def test_proxy(self):
        proxy_url = self.get_url()
        try :
            r = requests.get("http://httpbin.org/ip", proxies={"http":proxy_url, "https":proxy_url}, timeout=5)
        except:
            return False
        return (r.json()['origin'].split(',')[0] == self.host)

if __name__ == "__main__" :
    # proxies = ["108.61.186.207:8080","118.27.31.50:3128","5.196.132.117:3128"]
    # proxymanager = ProxyManager(proxies)
    proxymanager = ProxyManager.from_file("proxies")
    random_proxy = proxymanager.get_random_proxy() 
    print(random_proxy, random_proxy.test_proxy())
    proxymanager.to_file('test')