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

from pybossa.pro_features import ProFeatureHandler
from mock import Mock, patch, PropertyMock
from pybossa.model.user import User


def mock_current_user(anonymous=True, admin=None, id=None, pro=False):
    mock = Mock(spec=User)
    mock.is_anonymous = anonymous
    mock.is_authenticated = not anonymous
    if anonymous:
        type(mock).admin = PropertyMock(side_effect=AttributeError)
        type(mock).pro = PropertyMock(side_effect=AttributeError)
        type(mock).id = PropertyMock(side_effect=AttributeError)
    else:
        mock.admin = admin
        mock.pro = pro
        mock.id = id
    return mock


class TestContributionsGuard(object):

    def setUp(self):
        self.config_enabled = {
            'auditlog':              True,
            'webhooks':              True,
            'updated_exports':       True,
            'notify_blog_updates':   True,
            'project_weekly_report': True,
            'autoimporter':          True,
            'better_stats':          True
        }
        self.config_disabled = {
            'auditlog':              False,
            'webhooks':              False,
            'updated_exports':       False,
            'notify_blog_updates':   False,
            'project_weekly_report': False,
            'autoimporter':          False,
            'better_stats':          False
        }
        self.admin = mock_current_user(anonymous=False, id=1, admin=True)
        self.pro = mock_current_user(anonymous=False, id=2, pro=True)
        self.no_pro = mock_current_user(anonymous=False, id=3, pro=False, admin=False)
        self.anonymous = mock_current_user(anonymous=True)

    def test_auditlog_enabled_for_admin_always_returns_True(self):
        pro_enabled_handler = ProFeatureHandler(self.config_enabled)

        assert pro_enabled_handler.auditlog_enabled_for(self.admin) is True

        pro_disabled_handler = ProFeatureHandler(self.config_disabled)

        assert pro_disabled_handler.auditlog_enabled_for(self.admin) is True

    def test_auditlog_enabled_for_pro_always_returns_True(self):
        pro_enabled_handler = ProFeatureHandler(self.config_enabled)

        assert pro_enabled_handler.auditlog_enabled_for(self.pro) is True

        pro_disabled_handler = ProFeatureHandler(self.config_disabled)

        assert pro_disabled_handler.auditlog_enabled_for(self.pro) is True

    def test_auditlog_enabled_for_non_pro_returns_False_if_enabled(self):
        pro_enabled_handler = ProFeatureHandler(self.config_enabled)

        assert pro_enabled_handler.auditlog_enabled_for(self.no_pro) is False

    def test_auditlog_enabled_for_non_pro_returns_True_if_disabled(self):
        pro_disabled_handler = ProFeatureHandler(self.config_disabled)

        assert pro_disabled_handler.auditlog_enabled_for(self.no_pro) is True


    def test_webhooks_enabled_for_admin_always_returns_True(self):
        pro_enabled_handler = ProFeatureHandler(self.config_enabled)

        assert pro_enabled_handler.webhooks_enabled_for(self.admin) is True

        pro_disabled_handler = ProFeatureHandler(self.config_disabled)

        assert pro_disabled_handler.webhooks_enabled_for(self.admin) is True

    def test_webhooks_enabled_for_pro_always_returns_True(self):
        pro_enabled_handler = ProFeatureHandler(self.config_enabled)

        assert pro_enabled_handler.webhooks_enabled_for(self.pro) is True

        pro_disabled_handler = ProFeatureHandler(self.config_disabled)

        assert pro_disabled_handler.webhooks_enabled_for(self.pro) is True

    def test_webhooks_enabled_for_non_pro_returns_False_if_enabled(self):
        pro_enabled_handler = ProFeatureHandler(self.config_enabled)

        assert pro_enabled_handler.webhooks_enabled_for(self.no_pro) is False

    def test_webhooks_enabled_for_non_pro_returns_True_if_disabled(self):
        pro_disabled_handler = ProFeatureHandler(self.config_disabled)

        assert pro_disabled_handler.webhooks_enabled_for(self.no_pro) is True


    def test_autoimporter_enabled_for_admin_always_returns_True(self):
        pro_enabled_handler = ProFeatureHandler(self.config_enabled)

        assert pro_enabled_handler.autoimporter_enabled_for(self.admin) is True

        pro_disabled_handler = ProFeatureHandler(self.config_disabled)

        assert pro_disabled_handler.autoimporter_enabled_for(self.admin) is True

    def test_autoimporter_enabled_for_pro_always_returns_True(self):
        pro_enabled_handler = ProFeatureHandler(self.config_enabled)

        assert pro_enabled_handler.autoimporter_enabled_for(self.pro) is True

        pro_disabled_handler = ProFeatureHandler(self.config_disabled)

        assert pro_disabled_handler.autoimporter_enabled_for(self.pro) is True

    def test_autoimporter_enabled_for_non_pro_returns_False_if_enabled(self):
        pro_enabled_handler = ProFeatureHandler(self.config_enabled)

        assert pro_enabled_handler.autoimporter_enabled_for(self.no_pro) is False

    def test_autoimporter_enabled_for_non_pro_returns_True_if_disabled(self):
        pro_disabled_handler = ProFeatureHandler(self.config_disabled)

        assert pro_disabled_handler.autoimporter_enabled_for(self.no_pro) is True


    def test_better_stats_enabled_for_admin_user_always_returns_True(self):
        pro_enabled_handler = ProFeatureHandler(self.config_enabled)

        assert pro_enabled_handler.better_stats_enabled_for(self.admin, self.no_pro) is True

        pro_disabled_handler = ProFeatureHandler(self.config_disabled)

        assert pro_disabled_handler.better_stats_enabled_for(self.admin, self.no_pro) is True

    def test_better_stats_enabled_for_pro_owner_always_returns_True(self):
        pro_enabled_handler = ProFeatureHandler(self.config_enabled)

        assert pro_enabled_handler.better_stats_enabled_for(self.no_pro, self.pro) is True
        assert pro_enabled_handler.better_stats_enabled_for(self.anonymous, self.pro) is True

        pro_disabled_handler = ProFeatureHandler(self.config_disabled)

        assert pro_disabled_handler.better_stats_enabled_for(self.no_pro, self.pro) is True
        assert pro_disabled_handler.better_stats_enabled_for(self.anonymous, self.pro) is True

    def test_better_stats_enabled_for_non_pro_owner_and_non_pro_user_returns_False_if_enabled(self):
        pro_enabled_handler = ProFeatureHandler(self.config_enabled)

        assert pro_enabled_handler.better_stats_enabled_for(self.no_pro, self.no_pro) is False

    def test_better_stats_enabled_for_non_pro_owner_and_non_pro_user_returns_True_if_disabled(self):
        pro_disabled_handler = ProFeatureHandler(self.config_disabled)

        assert pro_disabled_handler.better_stats_enabled_for(self.no_pro, self.no_pro) is True

    def test_better_stats_enabled_for_non_pro_owner_and_anonym_user_returns_False_if_enabled(self):
        pro_enabled_handler = ProFeatureHandler(self.config_enabled)

        assert pro_enabled_handler.better_stats_enabled_for(self.anonymous, self.no_pro) is False

    def test_better_stats_enabled_for_non_pro_owner_and_anonym_user_returns_True_if_disabled(self):
        pro_disabled_handler = ProFeatureHandler(self.config_disabled)

        assert pro_disabled_handler.better_stats_enabled_for(self.anonymous, self.no_pro) is True


    def test_only_for_pro_returns_True_if_feature_is_only_for_pro(self):
        pro_enabled_handler = ProFeatureHandler(self.config_enabled)

        assert pro_enabled_handler.only_for_pro('auditlog') is True

    def test_only_for_pro_returns_False_if_feature_is_for_everyone(self):
        pro_disabled_handler = ProFeatureHandler(self.config_disabled)

        assert pro_disabled_handler.only_for_pro('auditlog') is False
