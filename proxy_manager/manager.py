import asyncio
import logging
import datetime
import random

from proxy_manager.proxy import Proxy
from proxy_manager.sources import ClarketmSource, A2uSource, TheSpeedXSource, HttpTunnelGe, ProxyTimeRu

LOGGER = logging.getLogger("proxy_manager")
LOGGER.setLevel(logging.INFO)
LOGGER.addHandler(logging.StreamHandler())

class ProxyManager():
    """Holds a list of proxies and handling tools"""
    def __init__(self, good_proxy_list, export_files, fail_limit=3, sources=[ClarketmSource, A2uSource, TheSpeedXSource, HttpTunnelGe, ProxyTimeRu]):
        # for now assume we just instanciate with good proxies
        self.good_proxies = set(good_proxy_list)
        self.bad_proxies = set()
        self.banned_proxies = set()
        self.export_files = export_files
        self.consecutive_fail_limit = fail_limit
        self.sources = sources

    @classmethod
    def import_proxy_manager(cls, export_files, fail_limit=3):
        proxy_manager = cls(set(), export_files, fail_limit)
        with open(export_files["good_proxies"]) as proxy_import:
            for line in proxy_import.readlines():
                proxy_manager.good_proxies.add(Proxy.import_proxy(line))
        with open(export_files["bad_proxies"]) as proxy_import:
            for line in proxy_import.readlines():
                proxy_manager.bad_proxies.add(Proxy.import_proxy(line))
        with open(export_files["banned_proxies"]) as proxy_import:
            for line in proxy_import.readlines():
                proxy_manager.banned_proxies.add(Proxy.import_proxy(line))
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
                self.good_proxies.add(good_proxy)
        for banned_proxy in other.banned_proxies:
            if banned_proxy not in (self.good_proxies + self.bad_proxies + self.banned_proxies):
                self.banned_proxies.add(banned_proxy)
        for bad_proxy in other.bad_proxies:
            if bad_proxy not in (self.good_proxies + self.bad_proxies + self.banned_proxies):
                self.bad_proxies.add(bad_proxy)

    @classmethod
    def proxies_from_hosts_ports(cls, hosts_ports):
        proxies = {Proxy(h, p) for (h, p) in hosts_ports}
        return proxies

    async def handle_proxy(self, proxy, require_anonymity = False):
        proxy_is_good = await proxy.test(require_anonymity)
        if proxy_is_good:
            self.good_proxies.add(proxy)
            LOGGER.info("[Proxy Manager] adding good proxy %s", str(proxy))
        else:
            self.bad_proxies.add(proxy)
            LOGGER.info("[Proxy Manager] adding bad proxy %s", str(proxy))

    def import_proxy_set(self, proxy_set, require_anonymity=False):
        async def main():
            tasks = []
            known_proxies = (self.good_proxies | self.bad_proxies | self.banned_proxies)
            for proxy in proxy_set:
                if proxy not in known_proxies:
                    tasks.append(asyncio.ensure_future(self.handle_proxy(proxy, require_anonymity)))
                # else:
                #     LOGGER.info("[Proxy Manager] already knew %s", str(proxy))

            await asyncio.gather(*tasks)

        # for now keep asyncio foothold to a minimum
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
        loop.close()

    def fetch_sources(self, require_anonymity=False):
        proxies = set()
        for source in self.sources:
            hosts_ports = source.fetch()
            proxies.update(self.proxies_from_hosts_ports(hosts_ports))
        self.import_proxy_set(proxies, require_anonymity)

    def check_bad_proxies(self, require_anonymity=False):
        bad_proxies = self.bad_proxies
        self.bad_proxies = set()

        self.import_proxy_set(bad_proxies, require_anonymity)        

    def check_good_proxies(self, require_anonymity=False):
        good_proxies = self.good_proxies
        self.good_proxies = set()

        self.import_proxy_set(good_proxies, require_anonymity)        

    def __repr__(self):
        return str(self.good_proxies)

    def good_proxy_count(self):
        return len(self.good_proxies)

    def get_random_good_proxy(self):
        try:
            good_proxy = random.choice(tuple(self.good_proxies))
        except IndexError:
            LOGGER.error("[Proxy Manager] No more good proxies")
            return None
        return good_proxy

    def get_random_bad_proxy(self):
        try:
            bad_proxy = random.choice(tuple(self.bad_proxies))
        except IndexError:
            LOGGER.error("[Proxy Manager] No bad proxy in manager")
            return None
        return bad_proxy

    def succeed_proxy(self, proxy):
        proxy.succeed()
        return

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
            self.banned_proxies.add(proxy)
        else:
            LOGGER.info("[Proxy Manager] %s already banned", str(proxy))
        return

    def unban_proxy(self, proxy):
        LOGGER.info("[Proxy Manager] unbanning %s", str(proxy))
        proxy.unban()
        if proxy in self.banned_proxies:
            self.banned_proxies.remove(proxy)
            self.good_proxies.add(proxy)
        else:
            LOGGER.info("[Proxy Manager] %s already unbanned", str(proxy))
        return

    def remove_bad_proxy(self, proxy):
        LOGGER.info("[Proxy Manager] Removing %s", str(proxy))
        if proxy in self.good_proxies:
            self.good_proxies.remove(proxy)
            self.bad_proxies.add(proxy)
        else:
            LOGGER.info("[Proxy Manager] %s already removed", str(proxy))
        return

    def unban_oldest(self, hour_delta):
        unban_set = set()
        for proxy in self.banned_proxies:
            if (datetime.datetime.now() - proxy.bans[-1]) > datetime.timedelta(hours=hour_delta):
                unban_set.add(proxy)
        # have to separate to avoid modifying list within loop
        for proxy in unban_set:
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

    # print(proxymanager.get_random_good_proxy())

    # proxymanager.fetch_sources(require_anonymity = False)
    old_len = len(proxymanager.good_proxies)
    proxymanager.check_bad_proxies(require_anonymity = False)
    new_len = len(proxymanager.good_proxies)
    print(old_len, new_len)

    old_len = len(proxymanager.good_proxies)
    proxymanager.check_good_proxies(require_anonymity = False)
    new_len = len(proxymanager.good_proxies)
    print(old_len, new_len)


    proxymanager.export_proxy_manager()