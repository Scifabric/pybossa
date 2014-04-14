import redis


class Sentinel(object):

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.connection = redis.sentinel.Sentinel(app.config['REDIS_SENTINEL'],
                                                  socket_timeout=0.1)
        self.master = self.connection.master_for('mymaster')
        self.slave = self.connection.slave_for('mymaster')
