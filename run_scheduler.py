import os
from redis import StrictRedis
from redis.sentinel import Sentinel
from rq_scheduler.scheduler import Scheduler
from rq.logutils import setup_loghandlers
from flask import Flask
from time import sleep


def run_scheduler():
    setup_loghandlers('DEBUG')

    app = Flask('sched_config')

    app.config.from_envvar('PYBOSSA_SETTINGS', silent=True)
    if not os.environ.get('PYBOSSA_SETTINGS'):
        here = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(here, 'settings_local.py')
        if os.path.exists(config_path):
            app.config.from_pyfile(config_path)

    db = app.config.get('REDIS_DB', 0)
    if all(app.config.get(attr) for attr in
        ['REDIS_MASTER_DNS', 'REDIS_PORT']):
        master = StrictRedis(host=app.config['REDIS_MASTER_DNS'],
            port=app.config['REDIS_PORT'], db=db)
    else:
        sentinel = Sentinel(app.config['REDIS_SENTINEL'])
        master = sentinel.master_for(app.config['REDIS_MASTER'], db=db)
    scheduler = Scheduler(connection=master)
    while True:
        try:
            scheduler.run()
        except ValueError:
            sleep(600)


if __name__ == '__main__':
    run_scheduler()
