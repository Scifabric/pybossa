import os
from redis import StrictRedis
from redis.sentinel import Sentinel
from rq_scheduler.scheduler import Scheduler
from rq.logutils import setup_loghandlers
from flask import Flask
from time import sleep
import app_settings

def run_scheduler():
    setup_loghandlers('DEBUG')
    db = app_settings.config.get('REDIS_DB', 0)
    if all(app_settings.config.get(attr) for attr in
        ['REDIS_MASTER_DNS', 'REDIS_PORT']):
        master = StrictRedis(host=app_settings.config['REDIS_MASTER_DNS'],
            port=app_settings.config['REDIS_PORT'], db=db)
    else:
        sentinel = Sentinel(app_settings.config['REDIS_SENTINEL'])
        master = sentinel.master_for(app_settings.config['REDIS_MASTER'], db=db)
    scheduler = Scheduler(connection=master)
    while True:
        try:
            scheduler.run()
        except ValueError:
            sleep(600)


if __name__ == '__main__':
    run_scheduler()
