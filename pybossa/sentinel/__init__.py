from redis import sentinel


class Sentinel(object):

    def __init__(self, app=None):
        self.app = app
        if app is not None: # pragma: no cover
            self.init_app(app)

    def init_app(self, app):
        self.connection = sentinel.Sentinel(app.config['REDIS_SENTINEL'],
                                                  socket_timeout=0.1)
        redis_db = app.config['REDIS_DB'] or 0
        self.master = self.connection.master_for('mymaster', db=redis_db)
        self.slave = self.connection.slave_for('mymaster', db=redis_db)
