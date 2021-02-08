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
from get_formatted_error import GetFormattedError
from lib.base_action import BaseAction
from st2common.runners.base_action import Action
import mock

__all__ = [
    'TestGetFormattedError'
]


class TestGetFormattedError(ErrorsBaseActionTestCase):
    __test__ = True
    action_cls = GetFormattedError

    def test_init(self):
        action = self.get_action_instance({})
        self.assertIsInstance(action, GetFormattedError)
        self.assertIsInstance(action, BaseAction)
        self.assertIsInstance(action, Action)

    @mock.patch("lib.base_action.BaseAction.st2_client_initialize")
    @mock.patch("get_formatted_error.GetFormattedError.find_error_execution")
    @mock.patch("get_formatted_error.GetFormattedError.format_error")
    def test_run_html(self,
                      mock_format_error,
                      mock_find_error_execution,
                      mock_st2_client_initialize):

        action = self.get_action_instance({})
        kwargs_dict = {
            'st2_exe_id': '1234',
            'html_tags': True,
            'ignored_error_tasks': ['send_error_email', 'provision_cleanup_exec']
        }

        test_error_result = {
            'result': 'None',
            'stderr': 'test_error'
        }
        mock_context = {
            'orquesta': {
                'task_name': 'vsphere_check'
            }
        }
        test_execution = mock.Mock(id='123', context=mock_context, result=test_error_result)
        mock_st2_client_initialize.return_value = test_execution
        action.child_error = []
        action.parent_error = test_execution

        expected_return = ("Error task: vsphere_check<br>"
                           "Error execution ID: 123<br>"
                           "Error message: test_error<br>")

        mock_format_error.return_value = expected_return

        result = action.run(**kwargs_dict)
        self.assertEqual(result, expected_return)

    @mock.patch("lib.base_action.BaseAction.st2_client_initialize")
    @mock.patch("get_formatted_error.GetFormattedError.find_error_execution")
    @mock.patch("get_formatted_error.GetFormattedError.format_error")
    def test_run_returns(self,
                         mock_format_error,
                         mock_find_error_execution,
                         mock_st2_client_initialize):

        action = self.get_action_instance({})
        kwargs_dict = {
            'st2_exe_id': '1234',
            'html_tags': False,
            'ignored_error_tasks': ['send_error_email', 'provision_cleanup_exec']
        }

        test_error_result = {
            'result': 'None',
            'stderr': 'test_error'
        }
        mock_context = {
            'orquesta': {
                'task_name': 'vsphere_check'
            }
        }
        test_execution = mock.Mock(id='123', context=mock_context, result=test_error_result)
        mock_st2_client_initialize.return_value = test_execution
        action.child_error = []
        action.parent_error = test_execution

        expected_return = ("Error task: vsphere_check"
                           "Error execution ID: 123"
                           "Error message: test_error")

        mock_format_error.return_value = expected_return

        result = action.run(**kwargs_dict)
        self.assertEqual(result, expected_return)
