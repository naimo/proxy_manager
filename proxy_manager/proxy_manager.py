"""This module helps cycling proxies for web scraping applications"""

import random
import requests
import datetime

class ProxyManager():
    """Holds a list of proxies and handling tools"""
    def __init__(self, proxy_list):
        self.proxies = [Proxy(h, p) for (h, p) in [p.split(':') for p in proxy_list]]

    @classmethod
    def from_file(cls, filename):
        with open(filename) as proxy_file:
            content = proxy_file.readlines()
        content = [x.strip() for x in content]
        return cls(content)

    def get_random_proxy(self):
        return random.choice(self.proxies)

    def remove_proxy(self, proxy):
        self.proxies.remove(proxy)

    def add_proxy(self, proxy):
        self.proxies.append(proxy)

    def to_file(self, filename):
        with open(filename, 'w') as export_file:
            export_file.write('\n'.join([str(p) for p in self.proxies]))

class Proxy():
    """Single proxy class, with helper functions"""
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.successes = 0
        self.fails = 0
        self.consecutive_fails = 0
        self.bans = [None]

    def __eq__(self, other):
        if isinstance(other, Proxy):
            return (self.host == other.host) and (self.port == other.port)
        return False

    def __repr__(self):
        return self.get_url()

    def get_url(self):
        return self.host+":"+str(self.port)

    def ban(self):
        self.bans[-1] = datetime.datetime.now()
        return

    def unban(self):
        self.bans.append(None)
        return

    def is_banned(self):
        return self.bans[-1] is not None

    def fail(self):
        self.fails += 1
        self.consecutive_fails += 1
        return

    def succeed(self):
        self.successes += 1
        self.consecutive_fails = 0
        return

    def stats(self):
        total = self.successes+self.fails
        if total>0:
            success_ratio = self.successes/(self.successes+self.fails)
        else:
            success_ratio = 1
        return success_ratio,self.consecutive_fails

    def last_ban_hours(self):
        if self.is_banned():
            ban_hours = (datetime.datetime.now() - self.bans[-1]).seconds/3600
            return ban_hours

    def test(self):
        proxy_url = self.get_url()
        try:
            response = requests.get("http://httpbin.org/ip",
                                    proxies={"http":proxy_url, "https":proxy_url}, timeout=5)
        except:
            return False
        ip_check = response.json()['origin'].split(',')[0] == self.host
        if ip_check:
            self.succeed()
        else:
            self.fail()
        return ip_check

if __name__ == "__main__":
    # proxies = ["108.61.186.207:8080","118.27.31.50:3128","5.196.132.117:3128"]
    # proxymanager = ProxyManager(proxies)
    proxymanager = ProxyManager.from_file("proxies")

    random_proxy = proxymanager.get_random_proxy()

    print(random_proxy, random_proxy.test())
    print(random_proxy.is_banned())
    random_proxy.ban()
    print(random_proxy.is_banned(), random_proxy.last_ban_hours())
    random_proxy.unban()
    print(random_proxy.is_banned(), random_proxy.bans)

    print(random_proxy.stats())
    random_proxy.succeed()
    print(random_proxy.stats())
    random_proxy.fail()
    random_proxy.fail()
    print(random_proxy.stats())
    random_proxy.succeed()
    print(random_proxy.stats())
    random_proxy.fail()
    print(random_proxy.stats())

    proxymanager.to_file('test')
