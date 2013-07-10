from flask.ext.login import current_user


def create(app=None):
    return not current_user.is_anonymous()


def read(app=None):
    if app.hidden:
        if current_user.is_anonymous():
            return False
        if current_user.is_authenticated() and app.owner.id != current_user.id:
            return False
        if current_user.is_authenticated() and not current_user.admin:
            return False
        if current_user.is_authenticated() and app.owner.id == current_user.id:
            return True
    return True


def update(app):
    if not current_user.is_anonymous() and (app.owner_id == current_user.id
                                            or current_user.admin is True):
        return True
    else:
        return False


def delete(app):
    return update(app)
