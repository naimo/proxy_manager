import asyncio, aiohttp
import logging
import json
import datetime
import requests

LOGGER = logging.getLogger("proxy_manager")

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
        proxy.host = dictionary["host"]
        proxy.port = dictionary["port"]
        proxy.successes = dictionary["successes"]
        proxy.fails = dictionary["fails"]
        proxy.consecutive_fails = dictionary["consecutive_fails"]
        proxy.bans = dictionary["bans"]
        proxy.bans = [datetime.datetime.strptime(ban, "%Y-%m-%d %H:%M:%S.%f")
                      if ban else None for ban in proxy.bans]
        return proxy

    def __hash__(self):
        return self.__str__().__hash__()

    def __eq__(self, other):
        if isinstance(other, Proxy):
            return (self.host == other.host) and (self.port == other.port)
        return False

    def __str__(self):
        return self.get_url()

    def json_string(self):
        return json.dumps(self.__dict__, default=str)

    def get_url(self):
        return 'http://'+self.host+':'+str(self.port)

    def ban(self):
        if not self.is_banned():
            self.bans[-1] = datetime.datetime.now()
        else:
            LOGGER.info("[Proxy] already banned")
        return

    def unban(self):
        if self.is_banned():
            self.bans.append(None)
        else:
            LOGGER.info("[Proxy] already unbanned")
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
        if total > 0:
            success_ratio = self.successes/(self.successes+self.fails)
        else:
            success_ratio = 1
        return success_ratio, self.consecutive_fails

    def last_ban_hours(self):
        if self.is_banned():
            ban_hours = (datetime.datetime.now() - self.bans[-1]).seconds/3600
            return ban_hours
        else:
            return None

    async def test(self, require_anonymity=False):
        LOGGER.info("[Proxy] testing proxy %s", str(self))
        proxy_url = self.get_url()
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get("http://httpbin.org/ip",
                                        proxy=proxy_url, timeout=5
                                        ) as response:
                    response_json = await response.json()
            except (
                json.decoder.JSONDecodeError,
                aiohttp.client_exceptions.ClientProxyConnectionError,
                aiohttp.client_exceptions.ServerDisconnectedError,
                aiohttp.client_exceptions.ContentTypeError,
                aiohttp.client_exceptions.ClientOSError,
                aiohttp.client_exceptions.ClientResponseError,
                aiohttp.client_exceptions.ClientPayloadError
                ):
                LOGGER.info("[Proxy] Proxy connection error")
                return False
            except asyncio.TimeoutError:
                LOGGER.info("[Proxy] Proxy connection timeout")
                return False
            success = False
            if response_json is not None and "origin" in response_json:
                success = True
                LOGGER.info("[Proxy] Connection success")          
                if require_anonymity:
                    if response_json['origin'].split(',')[0] == self.host:
                        LOGGER.info("[Proxy] Anonymity success")
                    else:
                        success = False
                        LOGGER.info("[Proxy] Anonymity fail")
            else:
                LOGGER.info("[Proxy] Malformed json")          
            return success