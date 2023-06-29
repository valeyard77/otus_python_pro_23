import redis
import time
import logging
from functools import wraps


def retry(max_attempts, timeout):
    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for counter in range(max_attempts+1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if counter < max_attempts:
                        logging.error(
                            f"func '{func.__name__}' call failed with '{e}', attempt ({counter + 1}/{max_attempts})")
                        time.sleep(timeout)
                    else:
                        raise ValueError("unable to connect to storage, cache will not available")

        return wrapper

    return decorate


class Store:
    """ Provides read/write data from storage and/or cache """
    MAX_RETRIES = 3
    TIMEOUT = 0.3

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, key_expire: int = 1800):
        self.key_expire = key_expire
        self.cache = {}
        self.rdb = redis.StrictRedis(host, port, db, socket_timeout=0.5, socket_connect_timeout=0.5)

    @property
    def is_connected(self) -> bool:
        try:
            return self.rdb.ping()
        except:
            return False

    @retry(max_attempts=MAX_RETRIES, timeout=TIMEOUT)
    def set(self, key, val):
        try:
            self.rdb.set(key, val, ex=self.key_expire)
        except redis.exceptions.TimeoutError:
            raise TimeoutError
        except redis.exceptions.ConnectionError:
            raise ConnectionError

    @retry(max_attempts=MAX_RETRIES, timeout=TIMEOUT)
    def get(self, key):
        try:
            return self.rdb.get(key)
        except redis.exceptions.TimeoutError:
            raise TimeoutError
        except redis.exceptions.ConnectionError:
            raise ConnectionError

    def cache_get(self, key):
        """ get the cache from the storage. if the storage is empty, take the data by key from the redis """
        try:
            return self.cache.get(key, self.get(key))
        except:
            return None

    def cache_set(self, key, val):
        """ Setting value to cache and storage """

        self.cache[key] = val

        try:
            self.set(key, val)
        except Exception as e:
            logging.error(f"there was an error writing the key to redis, {e}")

    def keys(self, pattern: str = "*"):
        return self.rdb.keys(pattern)


if __name__ == '__main__':
    st = Store()
    st.set("key", "val")
