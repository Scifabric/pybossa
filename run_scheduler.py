import settings_local as settings
from redis import StrictRedis
from redis.sentinel import Sentinel
from rq_scheduler.scheduler import Scheduler
from rq.logutils import setup_loghandlers


def run_scheduler():
    setup_loghandlers('DEBUG')

    db = getattr(settings, 'REDIS_DB', 0)
    if all(hasattr(settings, attr) for attr in
        ['REDIS_MASTER_DNS', 'REDIS_PORT']):
        master = StrictRedis(host=settings.REDIS_MASTER_DNS,
            port=settings.REDIS_PORT, db=db)
    else:
        sentinel = Sentinel(settings.REDIS_SENTINEL)
        master = sentinel.master_for(settings.REDIS_MASTER, db=db)
    scheduler = Scheduler(connection=master)
    scheduler.run()


if __name__ == '__main__':
    run_scheduler()
