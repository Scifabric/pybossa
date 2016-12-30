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

app = create_app(run_as_server=False)

# Provide queue names to listen to as arguments to this script,
# similar to rqworker
with app.app_context():
    with Connection(sentinel.master):
        qs = map(Queue, sys.argv[1:]) or [Queue()]

        w = Worker(qs)
        w.work()
