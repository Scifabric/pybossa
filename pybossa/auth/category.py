from flask.ext.login import current_user


def create(app=None):
    if current_user.is_authenticated():
        if current_user.admin is True:
            return True
        else:
            return False
    else:
        return False


def read(app=None):
    return True


def update(app):
    return create(app)


def delete(app):
    return create(app)
