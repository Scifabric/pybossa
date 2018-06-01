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

from requests import Request

from pybossa.http_signer import HttpSigner


SECRET = 'my-secret-key'
HEADER = 'X-Sig'


class TestHttpSigner(object):
    def setUp(self):
        self.none_signer = HttpSigner(None, HEADER)
        self.http_signer = HttpSigner(SECRET, HEADER)

    def test_none_signer_does_not_sign(self):
        req = Request('GET', 'http://example.com')
        req = self.none_signer(req)

        assert HEADER not in req.headers
        assert not self.http_signer.valid(req)

    def test_none_signer_does_not_sign_request_auth(self):
        req = Request(
            'GET', 'http://example.com', auth=self.none_signer)
        prepared = req.prepare()

        assert HEADER not in prepared.headers
        assert not self.http_signer.valid(req)

    def test_signs_request_valid(self):
        req = Request('GET', 'http://example.com')
        req = self.http_signer(req)
        assert req.headers.get(HEADER) == SECRET
        assert self.http_signer.valid(req)

    def test_signs_request_invalid(self):
        req = Request('GET', 'http://example.com')
        req.headers[HEADER] = 'not-my-secret-key'
        assert req.headers.get(HEADER) != SECRET
        assert not self.http_signer.valid(req)

    def test_signs_request_auth(self):
        req = Request(
            'GET', 'http://example.com', auth=self.http_signer)
        prepared = req.prepare()
        assert prepared.headers.get(HEADER) == SECRET
        assert self.http_signer.valid(prepared)
