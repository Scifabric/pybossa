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
import sys
from rq import Queue, Connection, Worker

from pybossa.core import create_app, sentinel

print("calling create app function", flush=True)
app = create_app(run_as_server=False)
print("returned from app", flush=True)
print("just before try", flush=True)
try:
    print("inside try", flush=True)
    # Provide queue names to listen to as arguments to this script,
    # similar to rqworker
    with app.app_context():
        print("Inside app context class", flush=True)
        with Connection(sentinel.master):
            print("before creating queue map", flush=True)
            qs = map(Queue, sys.argv[1:]) or [Queue()]
            print("before creating worker object", flush=True)
            w = Worker(qs)
            print("1",w.successful_job_count, flush=True)  # Number of jobs finished successfully
            print("2",w.failed_job_count, flush=True) # Number of failed jobs processed by this worker
            print("3",w.total_working_time, flush=True)  # Amount of time spent executing jobs (in seconds)
            w.work()
            print("4",w.successful_job_count, flush=True)  # Number of jobs finished successfully
            print("5",w.failed_job_count, flush=True) # Number of failed jobs processed by this worker
            print("6",w.total_working_time, flush=True)  # Amount of time spent executing jobs (in seconds)
        print("outside inner with", flush=True)
    print("outside outer with", flush=True)
except Exception as e: 
    logger.error('Failed to add worker: '+ str(e))
    print("error", flush=True)
