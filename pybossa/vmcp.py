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
"""VMCP module to support CernVM.

Sign the data in the given dictionary and return a new hash
that includes the signature.

@param $data Is a dictionary that contains the values to be signed
@param $salt Is the salt parameter passed via the cvm_salt GET parameter
@param $pkey Is the path to the private key file that will be used to
calculate the signature
"""
import rsa
import hashlib
import base64


def myquote(line):
    """Quote line."""
    valid = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_.~"
    escaped = ""
    for c in line:
        if c not in valid:
            escaped += "%%%.2X" % ord(c)
        else:
            escaped += c
    return escaped


def calculate_buffer(data, salt):
    """Compute buffer."""
    strBuffer = ""
    for k in sorted(data.keys()):

        # Handle the BOOL special case
        v = data[k]
        if type(v) == bool:  # pragma: no cover
            if v:
                v = 1
            else:
                v = 0
            data[k] = v

        # Update buffer
        strBuffer += "%s=%s\n" % (str(k).lower(), myquote(str(v)))

    # Append salt
    strBuffer += salt
    return strBuffer


def sign(data, salt, pkey):
    """Sign data."""
    strBuffer = calculate_buffer(data, salt)
    with open(pkey, 'r') as f:
        private_key_string = f.read()
    private_key = rsa.PrivateKey.load_pkcs1(private_key_string)
    data['signature'] = base64.b64encode(rsa.sign(strBuffer, private_key, 'SHA-512'))
    return data
