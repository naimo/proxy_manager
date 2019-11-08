import logging
import datetime
import random

from proxy_manager.proxy import Proxy

LOGGER = logging.getLogger("proxy_manager")
LOGGER.setLevel(logging.INFO)
LOGGER.addHandler(logging.StreamHandler())

class ProxyManager():
    """Holds a list of proxies and handling tools"""
    def __init__(self, good_proxy_list, export_files, fail_limit=3):
        # for now assume we just instanciate with good proxies
        self.good_proxies = good_proxy_list
        self.bad_proxies = []
        self.banned_proxies = []
        self.export_files = export_files
        self.consecutive_fail_limit = fail_limit

    @classmethod
    def create_from_csv(cls, filename, export_files, fail_limit=3):
        # for now assume we just import good proxies from CSV
        proxies = cls.proxies_from_csv(filename)
        return cls(proxies, export_files, fail_limit)

    @classmethod
    def proxies_from_lines(cls, proxies_string):
        hosts_ports = [x.strip().split(':') for x in proxies_string]
        proxies = [Proxy(h, p) for (h, p) in hosts_ports]
        return proxies

    @classmethod
    def proxies_from_csv(cls, filename):
        with open(filename) as proxy_file:
            content = proxy_file.readlines()
        proxies = cls.proxies_from_lines(content)
        return proxies        

    def import_string(self, proxies_string):
        new_proxies = self.proxies_from_lines(proxies_string.splitlines())
        self.import_proxy_list(new_proxies)

    def import_csv(self, filename):
        new_proxies = self.proxies_from_csv(filename)
        self.import_proxy_list(new_proxies)

    def import_proxy_list(self, proxy_list):
        for p in proxy_list:
            if p not in (self.good_proxies + self.bad_proxies + self.banned_proxies):
                self.good_proxies.append(p)
                LOGGER.info("[Proxy Manager] adding %s", str(p))

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

    def __repr__(self):
        return str(self.good_proxies)

    def good_proxy_count(self):
        return len(self.good_proxies)

    def get_random_good_proxy(self):
        try:
            good_proxy = random.choice(self.good_proxies)
        except IndexError:
            LOGGER.error("[Proxy Manager] No more good proxies")
            raise
        return good_proxy

    def fail_proxy(self, proxy):
        proxy.fail()
        LOGGER.info("[Proxy Manager] %s failed %d consecutive times",
                    str(proxy), proxy.consecutive_fails)
        (_, consecutive_fails) = proxy.stats()
        if consecutive_fails > self.consecutive_fail_limit:
            LOGGER.info("[Proxy Manager] %s fails too much", str(proxy))
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
    proxymanager = ProxyManager.create_from_csv('proxies',
                                         export_files={
                                             'good_proxies':'good_test',
                                             'bad_proxies':'bad_test',
                                             'banned_proxies':'banned_test'
                                         })

    random_proxy = proxymanager.get_random_good_proxy()

    print(random_proxy, random_proxy.test())
    print(random_proxy.is_banned())
    proxymanager.ban_proxy(random_proxy)
    proxymanager.ban_proxy(random_proxy)
    print(random_proxy.is_banned(), random_proxy.last_ban_hours())
    proxymanager.unban_proxy(random_proxy)
    proxymanager.unban_proxy(random_proxy)
    print(random_proxy.is_banned(), random_proxy.bans)

    print(random_proxy.stats())
    proxymanager.succeed_proxy(random_proxy)
    print(random_proxy.stats())
    proxymanager.fail_proxy(random_proxy)
    proxymanager.fail_proxy(random_proxy)
    proxymanager.fail_proxy(random_proxy)
    proxymanager.fail_proxy(random_proxy)
    proxymanager.fail_proxy(random_proxy)
    proxymanager.fail_proxy(random_proxy)
    print(random_proxy.stats())
    proxymanager.succeed_proxy(random_proxy)
    print(random_proxy.stats())
    proxymanager.fail_proxy(random_proxy)
    print(random_proxy.stats())

    proxymanager.export_proxy_manager()
