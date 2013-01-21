from flaskext.login import current_user


def create(taskrun=None):
    return True


def read(taskrun=None):
    return True


def update(taskrun):
    if current_user.is_anonymous():
        return False
    else:
        # User authenticated
        if current_user.admin:
            return True
        else:
            if taskrun.user is not None and taskrun.user.id == current_user.id:
                return True
            else:
                return False


def delete(app):
    return update(app)
