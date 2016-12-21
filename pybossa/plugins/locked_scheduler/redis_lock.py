from time import time
from datetime import timedelta


class LockManager(object):
    """
    Class to manage resource locks
    :param cache: a Redis connection
    :param duration: how long a lock is valid after being acquired
        if not released (in seconds)
    """
    def __init__(self, cache, duration):
        self._cache = cache
        self._duration = timedelta(seconds=duration)

    def acquire_lock(self, resource_id, client_id, limit):
        # TODO can lock access to hash
        """
        Acquire a lock on a resource.
        :param resource_id: resource on which lock is needed
        :param client_id: id of client needing the lock
        :param limit: how many client can access the resource concurrently
        :return: True if lock was successfully acquired, else False
        """
        timestamp = time()
        self._release_expired_locks(resource_id, timestamp)
        if self._cache.hexists(resource_id, client_id):
            return True
        num_acquired = len(self._cache.hkeys(resource_id))
        if num_acquired < limit:
            self._cache.hset(resource_id, client_id, timestamp)
            self._cache.expire(resource_id, self._duration)
            return True
        return False

    def has_lock(self, resource_id, client_id):
        """
        :param resource_id: resource on which lock is being held
        :param client_id: client id
        :return: True if client id holds a lock on the resource,
        False otherwise
        """
        exists = self._cache.hexists(resource_id, client_id)
        if not exists:
            return False
        time_str = self._cache.hget(resource_id, client_id)
        timestamp = float(time_str)
        now = time()
        expires_on = timestamp + self._duration.total_seconds()
        return expires_on > now

    def release_lock(self, resource_id, client_id):
        """
        :param resource_id: resource on which lock is being held
        :param client_id: id of client holding the lock
        :return: None
        """
        self._cache.hdel(resource_id, client_id)

    def _release_expired_locks(self, resource_id, now):
        locks = self._cache.hgetall(resource_id)
        to_delete = []
        for key, timestamp in locks.iteritems():
            timestamp = float(timestamp)
            if now - timestamp > self._duration.total_seconds():
                to_delete.append(key)
        if to_delete:
            self._cache.hdel(resource_id, *to_delete)
