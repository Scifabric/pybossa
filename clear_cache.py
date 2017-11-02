from redis.sentinel import Sentinel
from settings_local import REDIS_SENTINEL as RS
import settings_local as settings

sentinel = Sentinel(RS)
conn = sentinel.master_for('mymaster')
cache_items = conn.keys(pattern='{}*'.format(settings.REDIS_KEYPREFIX))
for item in cache_items:
    conn.delete(item)

