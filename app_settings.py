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

import imp
import os


def _load_module_file_as_dict(path):
    module = imp.load_source('module', path)
    return {
        name: getattr(module, name)
        for name in dir(module)
        if not name.startswith('__')
    }


def _load_config():
    config_path, config = None, {}
    upref_mdata_path, upref_mdata = None, {}
    if os.environ.get('PYBOSSA_SETTINGS'):
        config_path = os.path.abspath(os.environ.get('PYBOSSA_SETTINGS'))
    else:
        here = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(here, 'settings_local.py')
    if config_path and os.path.exists(config_path):
        config = _load_module_file_as_dict(config_path)
        upref_mdata_path = os.path.join(os.path.dirname(config_path), 'settings_upref_mdata.py')
        if os.path.exists(upref_mdata_path):
            upref_mdata = imp.load_source('upref_mdata', upref_mdata_path)
        else:
            upref_mdata_path = None
    else:
        config_path = None
    return config_path, config, upref_mdata_path, upref_mdata

config_path, config, upref_mdata_path, upref_mdata = _load_config()
