import inspect
from flask import abort
from flask.ext.login import current_user

import app
import task
import taskrun
import team
import category
import user

class Requirement(object):
    """ Checks a function call and raises an exception if the
    function returns a non-True value. """

    def __init__(self, wrapped):
        self.wrapped = wrapped

    def __getattr__(self, attr):
        real = getattr(self.wrapped, attr)
        return Requirement(real)

    def __call__(self, *args, **kwargs):
        fc = self.wrapped(*args, **kwargs)
        if fc is not True:
            if current_user.is_anonymous():
                raise abort(403)
            else:
                raise abort(401)
        return fc

    @classmethod
    def here(cls):
        module = inspect.getmodule(cls)
        return cls(module)

require = Requirement.here()
