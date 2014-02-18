from flask.ext.login import current_user


def create(rundata=None):
    return True


def read(rundata=None):
    return True


def update(rundata):
    if current_user.is_anonymous():
        return False
    else:
        # User authenticated
        if current_user.admin:
            return True
        else:
            if rundata.user is not None and rundata.user.id == current_user.id:
                return True
            else:
                return False


def delete(app):
    return update(app)
