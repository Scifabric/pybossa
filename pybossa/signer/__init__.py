from itsdangerous import URLSafeTimedSerializer
from werkzeug import generate_password_hash, check_password_hash


class Signer(object):

    def __init__(self, app=None):
        self.app = app
        if app is not None: # pragma: no cover
            self.init_app(app)


    def init_app(self, app):
        key = app.config['ITSDANGEROUSKEY']
        self.signer = URLSafeTimedSerializer(key)


    def loads(self, string, **kwargs):
        return self.signer.loads(string, **kwargs)


    def dumps(self, key, **kwargs):
        return self.signer.dumps(key, **kwargs)


    def generate_password_hash(self, password):
        return generate_password_hash(password)


    def check_password_hash(self, passwd_hash, password):
        return check_password_hash(passwd_hash, password)
