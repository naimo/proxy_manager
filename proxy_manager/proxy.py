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
        proxy.__dict__.update(dictionary)
        # transform datetime strings back to datetimes
        proxy.bans = [datetime.datetime.strptime(ban, "%Y-%m-%d %H:%M:%S.%f")
                      if ban else None for ban in proxy.bans]
        return proxy

    def __eq__(self, other):
        if isinstance(other, Proxy):
            return (self.host == other.host) and (self.port == other.port)
        return False

    def __str__(self):
        return self.get_url()

    def json_string(self):
        return json.dumps(self.__dict__, default=str)

    def get_url(self):
        return self.host+":"+str(self.port)

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

    def test(self):
        LOGGER.info("[Proxy] testing proxy %s", str(self))
        proxy_url = self.get_url()
        try:
            response = requests.get("http://httpbin.org/ip",
                                    proxies={"http":proxy_url, "https":proxy_url}, timeout=5)
            response_json = response.json()
        except json.decoder.JSONDecodeError:
            LOGGER.info("[Proxy] Json error %s" % response.text)
            return False
        except requests.exceptions.ConnectTimeout:
            LOGGER.info("[Proxy] Request timeout error")
            return False
        except requests.exceptions.ProxyError as error:
            LOGGER.info("[Proxy] Proxy error %s", str(error))
            return False
        except requests.exceptions.ReadTimeout:
            LOGGER.info("[Proxy] Server timeout")
            return False
        except requests.exceptions.TooManyRedirects:
            LOGGER.info("[Proxy] Too many redirects")
            return False
        ip_check = response_json['origin'].split(',')[0] == self.host
        if ip_check:
            self.succeed()
        else:
            self.fail()
        return ip_check