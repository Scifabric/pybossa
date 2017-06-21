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

import pybossa.vmcp as vmcp
from mock import patch, mock_open
import hashlib
import rsa
import base64
from default import assert_not_raises


class TestVMCP(object):

    def test_myquote(self):
        """Test myquote works."""
        # Valid char should be the same
        err_msg = "Valid chars should not be quoted"
        assert vmcp.myquote('a') == 'a', err_msg
        # Non-valid
        err_msg = "Non-Valid chars should be quoted"
        assert vmcp.myquote('%') == '%25', err_msg

    def test_calculate_buffer(self):
        """Test calculate_buffer works"""
        data = {"flags": 8,
                "name": "MyAwesomeVM",
                "ram": 512,
                "secret": "mg041na39123",
                "userData": "[amiconfig]\nplugins=cernvm\n[cernvm]\nusers=user:users;password",
                "vcpus": 1,
                "true": True,
                "false": False,
                "version": "1.5"}

        out = vmcp.calculate_buffer(data, 'salt')
        err_msg = "Salt should be appended to the string"
        assert 'salt' in out, err_msg
        err_msg = "Boolean True has to be converted to 1"
        assert "true=1" in out, err_msg
        err_msg = "Boolean False has to be converted to 0"
        assert "false=0" in out, err_msg


    def test_sign(self):
        """Test sign works."""
        # rsa_pk = M2Crypto.RSA.gen_key(2048, 65537)
        rsa_keys = rsa.newkeys(2048, 65537)
        rsa_pk = rsa_keys[1]
        rsa_pub = rsa_keys[0]
        salt = 'salt'
        data = {"flags": 8,
                "name": "MyAwesomeVM",
                "ram": 512,
                "secret": "mg041na39123",
                "userData": "[amiconfig]\nplugins=cernvm\n[cernvm]\nusers=user:users;password",
                "vcpus": 1,
                "version": "1.5"}
        strBuffer = vmcp.calculate_buffer(data, salt)
        
        with patch('rsa.PrivateKey.load_pkcs1', return_value=rsa_pk):
            with patch('pybossa.vmcp.open', mock_open(read_data=''), create=True) as m:
                out = vmcp.sign(data, salt, 'testkey')
                err_msg = "There should be a key named signature"
                assert out.get('signature'), err_msg

                err_msg = "The signature should not be empty"
                assert out['signature'] is not None, err_msg
                assert out['signature'] != '', err_msg

                err_msg = "The signature should be the same"
                signature = base64.b64decode(out['signature'])
                assert rsa.verify(strBuffer, signature, rsa_pub) == 1, err_msg

                # The output must be convertible into json object
                import json
                assert_not_raises(Exception, json.dumps, out)
