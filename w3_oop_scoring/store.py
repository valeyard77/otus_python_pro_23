import redis
import time
import logging
from functools import wraps


def retry(max_attempts, timeout):
    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for counter in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if counter <= max_attempts:
                        logging.error(
                            f"func '{func.__name__}' call failed with '{e}', attempt ({counter+1}/{max_attempts})")
                        time.sleep(timeout)
                    else:
                        logging.error("unable to connect to storage, cache will not available")

        return wrapper

    return decorate


class Store:
    """ Provides read/write data from storage and/or cache """

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, key_expire: int = 1800):
        self.key_expire = key_expire
        self.cache = {}
        self.rdb = redis.Redis(host, port, db, socket_timeout=0.5, socket_connect_timeout=0.5)

    @retry(max_attempts=3, timeout=0.3)
    def set(self, key, val):
        self.rdb.set(key, val, ex=self.key_expire)

    @retry(max_attempts=3, timeout=0.3)
    def get(self, key):
        return self.rdb.get(key)

    def cache_get(self, key):
        """ get the cache from the storage. if the storage is empty, take the data by key from the redis """
        try:
            return self.cache.get(key, self.get(key))
        except redis.RedisError:
            logging.error("")
            return None
        except AttributeError:
            return None

    def cache_set(self, key, val):
        """ Setting value to cache and storage """

        self.cache[key] = val

        try:
            self.set(key, val)
        except redis.RedisError:
            logging.error("there was an error writing the key to redis")
