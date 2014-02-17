# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2013 SF Isle of Man Limited
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

import M2Crypto
import hashlib
import base64

"""
Sign the data in the given dictionary and return a new hash
that includes the signature.

@param $data Is a dictionary that contains the values to be signed
@param $salt Is the salt parameter passed via the cvm_salt GET parameter
@param $pkey Is the path to the private key file that will be used to calculate the signature
"""


def myquote(line):
    valid = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_.~"
    escaped = ""
    for c in line:
        if c not in valid:
            escaped += "%%%.2X" % ord(c)
        else:
            escaped += c
    return escaped


def calculate_buffer(data, salt):
    strBuffer = ""
    for k in sorted(data.iterkeys()):

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
    strBuffer = calculate_buffer(data, salt)
    # Sign data
    rsa = M2Crypto.RSA.load_key(pkey)
    digest = hashlib.new('sha512', strBuffer).digest()

    # Append signature
    data['signature'] = base64.b64encode(rsa.sign(digest, "sha512"))
    data['digest'] = digest
    data['strBuffer'] = strBuffer

    # Return new data dictionary
    return data
