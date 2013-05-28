from flaskext.login import current_user


def create(user=None):
    if current_user.is_authenticated():
        if current_user.admin:
            return True
        else:
            return False
    else:
        return False


def read(user=None):
    return True


def update(user):
    return create(user)


def delete(user):
    return update(user)
