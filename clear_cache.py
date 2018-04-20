from redis.sentinel import Sentinel
from settings_local import REDIS_SENTINEL as RS
import settings_local as settings
from redis import StrictRedis

db = getattr(settings, 'REDIS_DB', 0)
if all(hasattr(settings, attr) for attr in
    ['REDIS_MASTER_DNS', 'REDIS_PORT']):
    conn = StrictRedis(host=settings.REDIS_MASTER_DNS,
        port=settings.REDIS_PORT, db=db)
else:
    sentinel = Sentinel(RS)
    conn = sentinel.master_for('mymaster')

cache_items = conn.keys(pattern='{}*'.format(settings.REDIS_KEYPREFIX))
for item in cache_items:
    conn.delete(item)
