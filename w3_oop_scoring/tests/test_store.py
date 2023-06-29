import unittest
from unittest.mock import patch
import fakeredis

import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import store


class RedisStoreTestSuite(unittest.TestCase):
    """ Tests for RedisStore class """

    @patch("redis.StrictRedis", fakeredis.FakeStrictRedis)
    def test_success_initalization(self):
        """ Test success initialization of the store """
        storage = store.Store()
        self.assertTrue(storage.is_connected)

    def test_failed_initialization(self):
        """ Test failed initialization of the store """

        storage = store.Store()
        self.assertEqual(storage.is_connected, False)

    @patch("redis.StrictRedis", fakeredis.FakeStrictRedis)
    def test_getting_value_to_redis(self):
        """ Test getting value from the redis """

        val = 'value'
        storage = store.Store()
        storage.set('test', val)
        self.assertEqual(storage.get('test').decode("UTF-8"), val)

    @patch("redis.StrictRedis", fakeredis.FakeStrictRedis)
    def test_getting_value_from_cache(self):
        """ Test getting value from the cache """

        val = 'value'
        key = 'key'
        storage = store.Store()
        storage.cache_set(key, val)
        self.assertEqual(storage.cache_get(key), val)

    @patch("redis.StrictRedis", fakeredis.FakeStrictRedis)
    def test_setting_value_with_expiration(self):
        """ Test expiration of the new key """

        val = 'value'
        key = 'key'
        storage = store.Store(key_expire=1)
        storage.set(key, val)
        time.sleep(2)
        self.assertIsNone(storage.get(key))

    def test_setting_value_redis_abscent(self):
        """ Test setting value if redis is abscent """

        val = 'value'
        key = 'key'
        storage = store.Store()
        with self.assertRaises(ValueError):
            storage.set(key, val)


if __name__ == "__main__":
    unittest.main()
