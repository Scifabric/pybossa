from flask.ext.login import current_user


def create(app=None):
    return not current_user.is_anonymous()


def read(app=None):
    if app.hidden:
        if current_user.is_anonymous():
            return False
        if current_user.is_authenticated():
            if current_user.admin:
                return True
            else:
                return False
            if current_user.id == app.owner.id:
                return True
            else:
                return False
    return True


def update(app):
    if not current_user.is_anonymous() and (app.owner_id == current_user.id
                                            or current_user.admin is True):
        return True
    else:
        return False


def delete(app):
    return update(app)
