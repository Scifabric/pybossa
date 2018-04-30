import jwt
import time


def value(value, **kwargs):
    return value


def request(field, **kwargs):
    return kwargs[field]


def timestamp(offset, **kwargs):
    return time.time() + offset


def path(base, **kwargs):
    kwargs['base'] = base
    return '{base}/{bucket}/{key}'.format(**kwargs)


def create_jwt(jwt_config, jwt_secret, method, bucket, key):
    kwargs = {
        'method': method,
        'bucket': bucket,
        'key': key
    }
    payload = {}
    for key, value_type, args in jwt_config:
        payload[key] = globals()[value_type](*args, **kwargs)

    return jwt.encode(payload, jwt_secret, algorithm='HS256')
