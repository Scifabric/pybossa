import logging
import os
from redis import StrictRedis
from redis.sentinel import Sentinel
from rq_scheduler.scheduler import Scheduler
from time import sleep
import app_settings


logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)


def run_scheduler():
    conn_kwargs = {
        'db': app_settings.config.get('REDIS_DB') or 0,
        'password': app_settings.config.get('REDIS_PWD')
    }
    if all(app_settings.config.get(attr) for attr in
        ['REDIS_MASTER_DNS', 'REDIS_PORT']):
        master = StrictRedis(host=app_settings.config['REDIS_MASTER_DNS'],
            port=app_settings.config['REDIS_PORT'], **conn_kwargs)
    else:
        sentinel = Sentinel(app_settings.config['REDIS_SENTINEL'])
        master = sentinel.master_for(app_settings.config['REDIS_MASTER'], **conn_kwargs)
    scheduler = Scheduler(connection=master)
    while True:
        try:
            scheduler.run()
        except ValueError:
            sleep(600)


if __name__ == '__main__':
    run_scheduler()
