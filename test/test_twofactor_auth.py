# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2016 SciFabric LTD.
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

from otpauth import OtpAuth
from mock import Mock, patch

class TestOTP():

   @patch('os.urandom', return_value='myrandnum123')
   def test_random_number(self, mock_urandom):
      assert mock_urandom() == 'myrandnum123'
    
   @patch('otpauth.OtpAuth.valid_totp', return_value=True)
   @patch('base64.b32encode', return_value='myb64randnum123')
   def test_verify_totp_is_correct(self, mock_urandom, mock_valid_totp):
      randnum = mock_urandom()
      assert randnum == 'myb64randnum123'
 
      mock_secret = Mock(spec=OtpAuth)
      assert isinstance(mock_secret, OtpAuth)

      secret = mock_secret(randnum.decode('utf-8')) 
      otp = secret.totp() 
      assert mock_valid_totp(otp) is True
       
   @patch('otpauth.OtpAuth.valid_totp', return_value=False)
   @patch('base64.b32encode', return_value='myb64randnum123')
   def test_verify_totp_is_incorrect(self, mock_urandom, mock_valid_totp):
      randnum = mock_urandom()
      assert randnum == 'myb64randnum123'
 
      mock_secret = Mock(spec=OtpAuth)
      assert isinstance(mock_secret, OtpAuth)

      secret = mock_secret(randnum.decode('utf-8')) 
      otp = secret.totp()
      assert mock_valid_totp(otp) is False 


