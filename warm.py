# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2014 SF Isle of Man Limited
#
# PyBossa is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyBossa is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PyBossa.  If not, see <http://www.gnu.org/licenses/>.

#!/usr/bin/env python
import sys
import optparse
import inspect

#import pybossa.model as model
from pybossa.core import create_app

app = create_app()


def warm_cache():
    '''Warm cache'''
    # Cache 3 pages
    pages = range(1, 4)
    with app.app_context():
        import pybossa.cache.apps as cached_apps
        import pybossa.cache.categories as cached_cat
        import pybossa.cache.users as cached_users
        # Cache top apps
        cached_apps.get_featured_front_page()
        cached_apps.get_top()
        for page in pages:
            apps, count = cached_apps.get_featured('featured',
                                                   page,
                                                   app.config['APPS_PER_PAGE'])
            for a in apps:
                cached_apps.get_app(a['short_name'])
                cached_apps.n_tasks(a['id'])
                cached_apps.overall_progress(a['id'])
                cached_apps.n_completed_tasks(a['id'])
                cached_apps.n_volunteers(a['id'])

        # Categories
        categories = cached_cat.get_used()
        for c in categories:
            for page in pages:
                 apps, count = cached_apps.get(c['short_name'],
                                               page,
                                               app.config['APPS_PER_PAGE'])
                 for a in apps:
                     cached_apps.get_app(a['short_name'])
                     cached_apps.n_tasks(a['id'])
                     cached_apps.overall_progress(a['id'])
                     cached_apps.n_completed_tasks(a['id'])
                     cached_apps.n_volunteers(a['id'])
        # Users
        cached_users.get_top()


## ==================================================
## Misc stuff for setting up a command line interface

def _module_functions(functions):
    local_functions = dict(functions)
    for k,v in local_functions.items():
        if not inspect.isfunction(v) or k.startswith('_'):
            del local_functions[k]
    return local_functions

def _main(functions_or_object):
    isobject = inspect.isclass(functions_or_object)
    if isobject:
        _methods = _object_methods(functions_or_object)
    else:
        _methods = _module_functions(functions_or_object)

    usage = '''%prog {action}

Actions:
    '''
    usage += '\n    '.join(
        [ '%s: %s' % (name, m.__doc__.split('\n')[0] if m.__doc__ else '') for (name,m)
        in sorted(_methods.items()) ])
    parser = optparse.OptionParser(usage)
    # Optional: for a config file
    # parser.add_option('-c', '--config', dest='config',
    #         help='Config file to use.')
    options, args = parser.parse_args()

    if not args or not args[0] in _methods:
        parser.print_help()
        sys.exit(1)

    method = args[0]
    if isobject:
        getattr(functions_or_object(), method)(*args[1:])
    else:
        _methods[method](*args[1:])

__all__ = [ '_main' ]

if __name__ == '__main__':
    _main(locals())
