"""This module helps cycling proxies for web scraping applications"""

import json

import random
import requests
import datetime

class ProxyManager():
    """Holds a list of proxies and handling tools"""
    def __init__(self, good_proxy_list):
        # for now assume we just instanciate with good proxies
        self.good_proxies = [Proxy(h, p) for (h, p) in [p.split(':') for p in good_proxy_list]]
        self.bad_proxies = []
        self.banned_proxies = []
        
    @classmethod
    def from_csv(cls, filename):
        # for now assume we just import good proxies from CSV
        with open(filename) as proxy_file:
            content = proxy_file.readlines()
        content = [x.strip() for x in content]
        return cls(content)      

    @classmethod
    def import_proxy_manager(cls, good_filename, bad_filename, banned_filename):
        pm = cls([])
        with open(good_filename) as proxy_import:
            for line in proxy_import.readlines():
                pm.good_proxies.append(Proxy.import_proxy(line))
        with open(bad_filename) as proxy_import:
            for line in proxy_import.readlines():
                pm.bad_proxies.append(Proxy.import_proxy(line))
        with open(banned_filename) as proxy_import:
            for line in proxy_import.readlines():
                pm.banned_proxies.append(Proxy.import_proxy(line))
        return pm

    def export_proxy_manager(self, good_filename, bad_filename, banned_filename):
        with open(good_filename, 'w') as export_file:
            export_file.write('\n'.join([str(p) for p in self.good_proxies]))
        with open(bad_filename, 'w') as export_file:
            export_file.write('\n'.join([str(p) for p in self.bad_proxies]))
        with open(banned_filename, 'w') as export_file:
            export_file.write('\n'.join([str(p) for p in self.banned_proxies]))
        return

    def __repr__(self):
        return str(self.proxies)

    def get_random_good_proxy(self):
        return random.choice(self.good_proxies)

    def fail_proxy(self, proxy):
        self.good_proxies.remove(proxy)
        self.bad_proxies.append(proxy)
        return

    def ban_proxy(self, proxy):
        proxy.ban()
        self.good_proxies.remove(proxy)
        self.banned_proxies.append(proxy)
        return

    def unban_proxy(self, proxy):
        proxy.unban()
        self.good_proxies.append(proxy)
        self.banned_proxies.remove(proxy)
        return

    def add_proxy(self, proxy):
        # for now assume we only want to add good proxy
        self.good_proxies.append(proxy)
        return

class Proxy():
    """Single proxy class, with helper functions"""
    def __init__(self, host="8.8.8.8", port=0):
        self.host = host
        self.port = port
        self.successes = 0
        self.fails = 0
        self.consecutive_fails = 0
        self.bans = [None]

    @classmethod
    def import_proxy(cls, line):
        dictionary = json.loads(line)
        proxy = cls()
        proxy.__dict__.update(dictionary)
        # transform datetime strings back to datetimes
        proxy.bans = [datetime.datetime.fromisoformat(ban) if ban else None for ban in proxy.bans]
        return proxy

    def __eq__(self, other):
        if isinstance(other, Proxy):
            return (self.host == other.host) and (self.port == other.port)
        return False

    def __str__(self):
        return json.dumps(self.__dict__, default=str)

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
            response_json = response.json()
        except json.decoder.JSONDecodeError:
            print("Json error %s" % response.text)
            return False
        except requests.exceptions.ConnectTimeout:
            print("Request timeout error")
            return False
        except requests.exceptions.ProxyError as error:
            print("Proxy error : {0}".format(error.strerror))
            return False
        except requests.exceptions.ReadTimeout:
            print("Server timeout")
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
    proxymanager = ProxyManager.from_csv("proxies")

    random_proxy = proxymanager.get_random_good_proxy()

    print(random_proxy, random_proxy.test())
    print(random_proxy.is_banned())
    proxymanager.ban_proxy(random_proxy)
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

    proxymanager.export_proxy_manager('good_test', 'bad_test', 'banned_test')

    pm2 = ProxyManager.import_proxy_manager('good_test', 'bad_test', 'banned_test')
    print(pm2.good_proxies)