# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2015 Scifabric LTD.
#
# PYBOSSA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PYBOSSA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PYBOSSA.  If not, see <http://www.gnu.org/licenses/>.

#!/usr/bin/env python
import os
import sys
import optparse
import inspect

#import pybossa.model as model
from pybossa.core import create_app

app = create_app()


def warm_cache():
    '''Warm cache'''
    # Disable cache, so we can refresh the data in Redis
    os.environ['PYBOSSA_REDIS_CACHE_DISABLED'] = '1'
    # Cache 3 pages
    apps_cached = []
    pages = range(1, 4)
    with app.app_context():
        import pybossa.cache.projects as cached_apps
        import pybossa.cache.categories as cached_cat
        import pybossa.cache.users as cached_users
        import pybossa.cache.project_stats  as stats

        def warm_app(id, short_name, featured=False):
            if id not in apps_cached:
                cached_apps.get_app(short_name)
                cached_apps.n_tasks(id)
                n_task_runs = cached_apps.n_task_runs(id)
                cached_apps.overall_progress(id)
                cached_apps.last_activity(id)
                cached_apps.n_completed_tasks(id)
                cached_apps.n_volunteers(id)
                if n_task_runs >= 1000 or featured:
                    print("Getting stats for %s as it has %s task runs" % (short_name, n_task_runs))
                    stats.get_stats(id)
                apps_cached.append(id)

        # Cache top projects
        apps = cached_apps.get_top()
        for a in apps:
            warm_app(a['id'], a['short_name'])
        for page in pages:
            apps = cached_apps.get_featured('featured', page,
                                            app.config['APPS_PER_PAGE'])
            for a in apps:
                warm_app(a['id'], a['short_name'], featured=True)

        # Categories
        categories = cached_cat.get_used()
        for c in categories:
            for page in pages:
                 apps = cached_apps.get(c['short_name'],
                                        page,
                                        app.config['APPS_PER_PAGE'])
                 for a in apps:
                     warm_app(a['id'], a['short_name'])
        # Users
        cached_users.get_leaderboard(app.config['LEADERBOARD'])


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
