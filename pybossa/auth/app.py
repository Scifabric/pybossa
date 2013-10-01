from flask.ext.login import current_user


def create(app=None):
    return not current_user.is_anonymous()


def read(app=None):
    if app is None:
        return True
    elif app.hidden:
        if current_user.is_authenticated():
            if current_user.admin:
                return True
            elif current_user.id == app.owner_id:
                return True
            else:
                return False
        else:
            return False
    else:
        return True


def update(app):
    if not current_user.is_anonymous() and (app.owner_id == current_user.id
                                            or current_user.admin is True):
        return True
    else:
        return False


def delete(app):
    return update(app)
