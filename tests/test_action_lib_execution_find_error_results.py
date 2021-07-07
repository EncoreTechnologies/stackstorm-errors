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
from execution_find_error_results import ExecutionFindErrorResults
from lib.base_action import BaseAction
from st2common.runners.base_action import Action
import mock

__all__ = [
    'TestExecutionFindErrorResults'
]


class TestExecutionFindErrorResults(ErrorsBaseActionTestCase):
    __test__ = True
    action_cls = ExecutionFindErrorResults

    def test_init(self):
        action = self.get_action_instance({})
        self.assertIsInstance(action, ExecutionFindErrorResults)
        self.assertIsInstance(action, BaseAction)
        self.assertIsInstance(action, Action)

    @mock.patch("lib.base_action.BaseAction.st2_client_initialize")
    @mock.patch("lib.base_action.BaseAction.find_error_execution")
    @mock.patch("lib.base_action.BaseAction.format_error")
    def test_check_status_failed(self,
                                 mock_format_error,
                                 mock_find_error_execution,
                                 mock_st2_client_initialize):

        action = self.get_action_instance({})
        action.provision_skip_list = ['vm_delete', 'provision_cleanup', 'provision_cleanup_exec']
        action.st2_exe_id = "test1"

        expected_result = {
            'st2_execution_id': 'test1',
            'st2_execution_status': 'failed',
            'st2_execution_comments': 'test_error'
        }

        test_task_list = [
            {
                'status': 'succeeded',
                'name': 'task1'
            },
            {
                'status': 'error',
                'name': 'task2'
            }
        ]
        mock_execution = mock.Mock(spec=True,
                                   id='test1',
                                   status='failed',
                                   action={'name': 'test_action1'},
                                   result={'task_list': test_task_list,
                                           'key1': 'val1',
                                           'key2': 'val2'})
        mock_format_error.return_value = 'test_error'
        result = action.check_status(mock_execution, action.st2_exe_id, action.provision_skip_list)
        self.assertEqual(result, expected_result)

    @mock.patch("lib.base_action.BaseAction.st2_client_initialize")
    @mock.patch("lib.base_action.BaseAction.find_error_execution")
    @mock.patch("lib.base_action.BaseAction.format_error")
    def test_check_status_unknown(self,
                                  mock_format_error,
                                  mock_find_error_execution,
                                  mock_st2_client_initialize):

        action = self.get_action_instance({})
        action.provision_skip_list = ['vm_delete', 'provision_cleanup', 'provision_cleanup_exec']
        action.st2_exe_id = "test1"

        expected_result = {
            'st2_execution_id': 'test1',
            'st2_execution_status': 'unknown',
            'st2_execution_comments': 'Could not find execution_id in database'
        }

        test_task_list = [
            {
                'status': 'succeeded',
                'name': 'task1'
            },
            {
                'status': 'error',
                'name': 'task2'
            }
        ]
        mock_execution = mock.Mock(spec=True,
                                   id='test1',
                                   status='test_status',
                                   action={'name': 'test_action1'},
                                   result={'task_list': test_task_list,
                                           'key1': 'val1',
                                           'key2': 'val2'})
        mock_format_error.return_value = 'test_error'
        result = action.check_status(mock_execution, action.st2_exe_id, action.provision_skip_list)
        self.assertEqual(result, expected_result)

    @mock.patch("lib.base_action.BaseAction.st2_client_initialize")
    def test_run_unknown(self,
                         mock_st2_client_initialize):

        action = self.get_action_instance({})
        kwargs_dict = {
            'st2_exe_id': 'test1',
            'provision_skip_list': ['vm_delete', 'provision_cleanup', 'provision_cleanup_exec']
        }

        expected_result = {
            'st2_execution_id': 'test1',
            'st2_execution_status': 'unknown',
            'st2_execution_comments': 'Could not find execution_id in database'
        }

        test_task_list = [
            {
                'status': 'succeeded',
                'name': 'task1'
            },
            {
                'status': 'error',
                'name': 'task2'
            }
        ]
        mock_execution = mock.Mock(spec=True,
                                   id='test1',
                                   status='test_status',
                                   action={'name': 'test_action1'},
                                   result={'task_list': test_task_list,
                                           'key1': 'val1',
                                           'key2': 'val2'})
        mock_st2_client_initialize.return_value = mock_execution
        action.st2_client = mock.Mock()
        result = action.run(**kwargs_dict)
        self.assertEqual(result, expected_result)

    @mock.patch("lib.base_action.BaseAction.st2_client_initialize")
    @mock.patch("lib.base_action.BaseAction.format_error")
    def test_run_fail(self,
                      mock_format_error,
                      mock_st2_client_initialize):

        action = self.get_action_instance({})
        kwargs_dict = {
            'st2_exe_id': 'test1',
            'provision_skip_list': ['vm_delete', 'provision_cleanup', 'provision_cleanup_exec']
        }

        expected_result = {
            'st2_execution_id': 'test1',
            'st2_execution_status': 'failed',
            'st2_execution_comments': 'test_error'
        }

        test_task_list = [
            {
                'status': 'succeeded',
                'name': 'task1'
            },
            {
                'status': 'error',
                'name': 'task2'
            }
        ]
        mock_execution = mock.Mock(spec=True,
                                   id='test1',
                                   status='failed',
                                   context='test_context',
                                   action={'name': 'test_action1'},
                                   result={'task_list': test_task_list,
                                           'key1': 'val1',
                                           'key2': 'val2'})
        mock_st2_client_initialize.return_value = mock_execution
        action.st2_client = mock.Mock()
        mock_format_error.return_value = "test_error"
        result = action.run(**kwargs_dict)
        self.assertEqual(result, expected_result)
