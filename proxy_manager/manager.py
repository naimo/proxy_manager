import logging
import datetime
import random
import re

from proxy_manager.proxy import Proxy
from proxy_manager.sources import ClarketmSource, A2uSource, TheSpeedXSource

LOGGER = logging.getLogger("proxy_manager")
LOGGER.setLevel(logging.INFO)
LOGGER.addHandler(logging.StreamHandler())

IP_PORT_PATTERN = re.compile("((?:[0-9]{1,3}\.){3}[0-9]{1,3}):([0-9]+)")

class ProxyManager():
    """Holds a list of proxies and handling tools"""
    def __init__(self, good_proxy_list, export_files, fail_limit=3, sources=[ClarketmSource, A2uSource, TheSpeedXSource]):
        # for now assume we just instanciate with good proxies
        self.good_proxies = good_proxy_list
        self.bad_proxies = []
        self.banned_proxies = []
        self.export_files = export_files
        self.consecutive_fail_limit = fail_limit
        self.sources = sources

    @classmethod
    def import_proxy_manager(cls, export_files, fail_limit=3):
        proxy_manager = cls([], export_files, fail_limit)
        with open(export_files["good_proxies"]) as proxy_import:
            for line in proxy_import.readlines():
                proxy_manager.good_proxies.append(Proxy.import_proxy(line))
        with open(export_files["bad_proxies"]) as proxy_import:
            for line in proxy_import.readlines():
                proxy_manager.bad_proxies.append(Proxy.import_proxy(line))
        with open(export_files["banned_proxies"]) as proxy_import:
            for line in proxy_import.readlines():
                proxy_manager.banned_proxies.append(Proxy.import_proxy(line))
        return proxy_manager

    def export_proxy_manager(self):
        with open(self.export_files["good_proxies"], 'w') as export_file:
            export_file.write('\n'.join([p.json_string() for p in self.good_proxies]))
        with open(self.export_files["bad_proxies"], 'w') as export_file:
            export_file.write('\n'.join([p.json_string() for p in self.bad_proxies]))
        with open(self.export_files["banned_proxies"], 'w') as export_file:
            export_file.write('\n'.join([p.json_string() for p in self.banned_proxies]))
        return

    def merge_proxy_manager(self, other):
        for good_proxy in other.good_proxies:
            if good_proxy not in (self.good_proxies + self.bad_proxies + self.banned_proxies):
                self.good_proxies.append(good_proxy)
        for banned_proxy in other.banned_proxies:
            if banned_proxy not in (self.good_proxies + self.bad_proxies + self.banned_proxies):
                self.banned_proxies.append(banned_proxy)
        for bad_proxy in other.bad_proxies:
            if bad_proxy not in (self.good_proxies + self.bad_proxies + self.banned_proxies):
                self.bad_proxies.append(bad_proxy)

    @classmethod
    def proxies_from_line_strings(cls, proxy_lines):
        hosts_ports = []
        for line in proxy_lines:
            m = IP_PORT_PATTERN.search(line)
            if m is not None:
                hosts_ports.append(m.groups())
        proxies = [Proxy(h, p) for (h, p) in hosts_ports]
        return proxies

    @classmethod
    def proxies_from_csv(cls, filename):
        with open(filename) as proxy_file:
            content = proxy_file.readlines()
        proxies = cls.proxies_from_line_strings(content)
        return proxies        

    def import_proxy_list(self, proxy_list, limit, require_anonymity=False):
        count = 0
        for p in proxy_list:
            if p not in (self.good_proxies + self.bad_proxies + self.banned_proxies):
                if p.test(require_anonymity):
                    self.good_proxies.append(p)
                    LOGGER.info("[Proxy Manager] adding good proxy %s", str(p))
                    if limit is not None:
                        count +=1
                        LOGGER.info("[Proxy Manager] %d/%d proxies found", count, limit)
                        if count == limit:
                            LOGGER.info("[Proxy Manager] enough proxies added")
                            return
                else:
                    self.bad_proxies.append(p)
                    LOGGER.info("[Proxy Manager] adding bad proxy %s", str(p))
            else:
                LOGGER.info("[Proxy Manager] already knew %s", str(p))

    def import_string(self, proxies_string, limit=None, require_anonymity=False):
        new_proxies = self.proxies_from_line_strings(proxies_string.splitlines())
        self.import_proxy_list(new_proxies, limit, require_anonymity)

    def import_csv(self, filename, limit=None, require_anonymity=False):
        new_proxies = self.proxies_from_csv(filename)
        self.import_proxy_list(new_proxies, limit, require_anonymity)

    def fetch_sources(self, limit=None, require_anonymity=False):
        proxies = []
        for source in self.sources:
            proxy_lines = source.fetch()
            proxies += (self.proxies_from_line_strings(proxy_lines))
        self.import_proxy_list(proxies, limit, require_anonymity)

    def __repr__(self):
        return str(self.good_proxies)

    def good_proxy_count(self):
        return len(self.good_proxies)

    def get_random_good_proxy(self):
        try:
            good_proxy = random.choice(self.good_proxies)
        except IndexError:
            LOGGER.error("[Proxy Manager] No more good proxies")
            return None
        return good_proxy

    def get_random_bad_proxy(self):
        try:
            bad_proxy = random.choice(self.bad_proxies)
        except IndexError:
            LOGGER.error("[Proxy Manager] No bad proxy in manager")
            return None
        return bad_proxy

    def fail_proxy(self, proxy):
        proxy.fail()
        LOGGER.info("[Proxy Manager] %s failed %d consecutive times",
                    str(proxy), proxy.consecutive_fails)
        (_, consecutive_fails) = proxy.stats()
        if consecutive_fails > self.consecutive_fail_limit:
            LOGGER.info("[Proxy Manager] %s fails too much, %d left", str(proxy), self.good_proxy_count())
            self.remove_bad_proxy(proxy)
        return

    def ban_proxy(self, proxy):
        LOGGER.info("[Proxy Manager] banning %s", str(proxy))
        proxy.ban()
        if proxy in self.good_proxies:
            self.good_proxies.remove(proxy)
            self.banned_proxies.append(proxy)
        else:
            LOGGER.info("[Proxy Manager] %s already banned", str(proxy))
        return

    def unban_proxy(self, proxy):
        LOGGER.info("[Proxy Manager] unbanning %s", str(proxy))
        proxy.unban()
        if proxy in self.banned_proxies:
            self.banned_proxies.remove(proxy)
            self.good_proxies.append(proxy)
        else:
            LOGGER.info("[Proxy Manager] %s already unbanned", str(proxy))
        return

    def succeed_proxy(self, proxy):
        proxy.succeed()
        return

    def remove_bad_proxy(self, proxy):
        LOGGER.info("[Proxy Manager] Removing %s", str(proxy))
        if proxy in self.good_proxies:
            self.good_proxies.remove(proxy)
            self.bad_proxies.append(proxy)
        else:
            LOGGER.info("[Proxy Manager] %s already removed", str(proxy))
        return

    def unban_oldest(self, hour_delta):
        unban_list = []
        for proxy in self.banned_proxies:
            if (datetime.datetime.now() - proxy.bans[-1]) > datetime.timedelta(hours=hour_delta):
                unban_list.append(proxy)
        # have to separate to avoid modifying list within loop
        for proxy in unban_list:
            self.unban_proxy(proxy)
        return

if __name__ == "__main__":
    # proxies = ["108.61.186.207:8080","118.27.31.50:3128","5.196.132.117:3128"]
    # proxymanager = ProxyManager(proxies)
    proxymanager = ProxyManager.import_proxy_manager(
                                         export_files={
                                             'good_proxies':'good_test',
                                             'bad_proxies':'bad_test',
                                             'banned_proxies':'banned_test'
                                         })

    random_good_proxy = proxymanager.get_random_good_proxy()
    if random_good_proxy is not None:
        print(random_good_proxy, random_good_proxy.test())
    else:
        print("No more good proxy")

    random_bad_proxy = proxymanager.get_random_bad_proxy()
    if random_bad_proxy is not None:
        print(random_bad_proxy, random_bad_proxy.test())
    else:
        print("No more bad proxy")

    proxymanager.fetch_sources(require_anonymity = False)

    proxymanager.export_proxy_manager()