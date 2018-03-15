from settings_local import REDIS_SENTINEL, REDIS_MASTER, REDIS_DB
from redis.sentinel import Sentinel
from rq_scheduler.scheduler import Scheduler
from rq.logutils import setup_loghandlers


def run_scheduler():
    setup_loghandlers('DEBUG')
    sentinel = Sentinel(REDIS_SENTINEL)
    master = sentinel.master_for(REDIS_MASTER, db=REDIS_DB)
    scheduler = Scheduler(connection=master)
    scheduler.run()


if __name__ == '__main__':
    run_scheduler()
