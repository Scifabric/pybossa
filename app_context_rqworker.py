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
from contextlib import contextmanager
import logging
import sys
import time
from traceback import print_exc

from rq import Queue, Connection, Worker
from rq.worker import logger

logger.setLevel(logging.DEBUG)

from pybossa.core import create_app, sentinel

app = create_app(run_as_server=False)
app.config['REDIS_SOCKET_TIMEOUT'] = 600

def retry(max_count):
    def decorator(func):
        def decorated(*args, **kwargs):
            count = 0
            while count < max_count:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print_exc(e)
                    count += 1
                    time.sleep(5**count)

        return decorated
    return decorator


@contextmanager
def get_worker(queues):
    worker = Worker(queues)
    try:
        yield worker
    finally:
        worker.register_death()


@retry(3)
def run_worker(queues, logger):
    with get_worker(queues) as w:
        try:
            w.log = logger
        except Exception:
            logger.warning('Unable to set logger')
        w.work()


# Provide queue names to listen to as arguments to this script,
# similar to rqworker
with app.app_context():
    with Connection(sentinel.master):
        qs = map(Queue, sys.argv[1:]) or [Queue()]

        run_worker(qs, app.logger)
