# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2018 Scifabric LTD.
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
"""Healthcheck for PYBOSSA."""
import json

from flask import Blueprint, Response

from pybossa.core import sentinel
from pybossa.core import db


blueprint = Blueprint('diagnostics', __name__)


def db_master():
    db.session.execute('SELECT 1;').fetchall()


def db_slave():
    db.slave_session.execute('SELECT 1;').fetchall()


def redis_master():
    sentinel.master.ping()


def redis_slave():
    sentinel.slave.ping()


checks = {
    'db_master': db_master,
    'db_slave': db_slave,
    'redis_master': redis_master,
    'redis_slave': redis_slave
}


def perform_check(check):
    try:
        check()
        return True
    except Exception:
        return False


def perform_checks():
    return {check: perform_check(fn) for check, fn in checks.iteritems()}


@blueprint.route('/')
@blueprint.route('/healthcheck')
def healthcheck():
    response = perform_checks()
    healthy =  all(response.itervalues())
    status = 200 if healthy else 500
    return Response(json.dumps(response), status=status,
                    mimetype='application/json')
