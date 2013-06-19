from flask.ext.login import current_user


def create(category=None):
    if current_user.is_authenticated():
        if current_user.admin is True:
            return True
        else:
            return False
    else:
        return False


def read(category=None):
    return True


def update(category):
    return create(category)


def delete(category):
    return create(category)
