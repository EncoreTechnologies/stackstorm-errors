#!/usr/bin/env python
# Copyright 2019 Encore Technologies
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from errors_base_action_test_case import ErrorsBaseActionTestCase

from lib.base_action import BaseAction
from st2common.runners.base_action import Action
import mock

__all__ = [
    'TestBaseAction'
]


class TestBaseAction(ErrorsBaseActionTestCase):
    __test__ = True
    action_cls = BaseAction

    def test_init(self):
        action = self.get_action_instance({})
        self.assertIsInstance(action, BaseAction)
        self.assertIsInstance(action, Action)

    @mock.patch("lib.base_action.Client")
    def test_st2_client_initialize(self, mock_client):
        action = self.get_action_instance({})

        mock_execution = mock.Mock(action={'ref': 'test_ref'}, status='test_status')
        mock_client_executions = mock.Mock()
        mock_client_executions.get_by_id.return_value = mock_execution
        mock_client.return_value = mock.Mock(executions=mock_client_executions)

        result = action.st2_client_initialize('1234')
        self.assertEqual(result, mock_execution)
