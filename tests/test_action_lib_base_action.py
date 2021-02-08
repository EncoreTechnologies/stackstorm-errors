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

    def test_find_error_execution(self):
        action = self.get_action_instance({})
        action.parent_error = None
        action.child_error = []
        mock_context = {
            'orquesta': {
                'task_name': 'vsphere_check'
            }
        }
        mock_execution_results = {
            'output': {
                'errors': ''
            }
        }
        test_ignored_tasks = []
        test_execution = mock.Mock(children=[],
                                   context=mock_context,
                                   status='failed',
                                   result=mock_execution_results)
        mock_client = mock.Mock()
        mock_client.executions.get_by_id.return_value = test_execution
        action.st2_client = mock_client

        mock_parent_execution = '1234'
        action.find_error_execution(mock_parent_execution, test_ignored_tasks)
        self.assertEqual(action.parent_error, test_execution)
        self.assertEqual(action.child_error, [])

    def test_find_error_execution_ignored_email(self):
        action = self.get_action_instance({})
        action.child_error = []
        mock_context = {
            'orquesta': {
                'task_name': 'send_error_email'
            }
        }
        test_ignored_tasks = ['send_error_email', 'provision_cleanup_exec']
        test_execution = mock.Mock(children=[], context=mock_context, status='failed')
        mock_client = mock.Mock()
        mock_client.executions.get_by_id.return_value = test_execution
        action.st2_client = mock_client
        action.parent_error = \
            action.st2_client.executions.get_by_id(mock_client.executions.get_by_id.return_value)

        mock_parent_execution = '1234'
        action.find_error_execution(mock_parent_execution, test_ignored_tasks)
        self.assertEqual(action.parent_error, test_execution)
        self.assertEqual(action.child_error, [])

    def test_find_error_execution_ignored_cleanup(self):
        action = self.get_action_instance({})
        action.child_error = []
        mock_context = {
            'orquesta': {
                'task_name': 'provision_cleanup_exec'
            }
        }
        test_ignored_tasks = ['send_error_email', 'provision_cleanup_exec']
        test_execution = mock.Mock(children=[], context=mock_context, status='failed')
        mock_client = mock.Mock()
        mock_client.executions.get_by_id.return_value = test_execution
        action.st2_client = mock_client
        action.parent_error = \
            action.st2_client.executions.get_by_id(mock_client.executions.get_by_id.return_value)

        mock_parent_execution = '1234'
        action.find_error_execution(mock_parent_execution, test_ignored_tasks)
        self.assertEqual(action.parent_error, test_execution)
        self.assertEqual(action.child_error, [])

    def check_custom_errors_true_string(self):
        action = self.get_action_instance({})
        test_execution_result = {
            'output': {
                'errors': 'test_error'
            }
        }
        test_execution = 'test_execution'
        expected_return = True
        result = action.check_custom_errors(test_execution_result, test_execution)
        self.assertEqual(result, expected_return)

    def check_custom_errors_true_array(self):
        action = self.get_action_instance({})
        test_execution_result = {
            'output': {
                'errors': ['test_error1', 'test_error2', 'test_error3']
            }
        }
        test_execution = 'test_execution'
        expected_return = True
        result = action.check_custom_errors(test_execution_result, test_execution)
        self.assertEqual(result, expected_return)

    def check_custom_errors_false(self):
        action = self.get_action_instance({})
        test_execution_result = {
            'output': {
                'test_key': 'test_value'
            }
        }
        test_execution = 'test_execution'
        expected_return = False
        result = action.check_custom_errors(test_execution_result, test_execution)
        self.assertEqual(result, expected_return)

    def test_format_error_parent_html(self):
        action = self.get_action_instance({})
        html_tags = True
        expected_result = ("Error task: vsphere_check<br>"
                           "Error execution ID: 123<br>"
                           "Error message: test_error<br>")
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
        action.child_error = []
        action.parent_error = test_execution
        result = action.format_error(html_tags)
        self.assertEqual(result, expected_result)

    def test_format_error_parent_returns(self):
        action = self.get_action_instance({})
        html_tags = False
        expected_result = ("Error task: vsphere_check\n"
                           "Error execution ID: 123\n"
                           "Error message: test_error\n")
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
        action.child_error = []
        action.parent_error = test_execution
        result = action.format_error(html_tags)
        self.assertEqual(result, expected_result)

    def test_format_error_child_html(self):
        action = self.get_action_instance({})
        html_tags = True
        expected_result = ("Error task: python_error<br>Error execution ID: 123<br>"
                           "Error message: test_error<br>Error task: bolt_error<br>"
                           "Error execution ID: 456<br>Error message: test_error<br>"
                           "Error task: jinja_error<br>Error execution ID: 789<br>"
                           "Error message: test_error<br>")
        test_error_result = {
            'result': 'None',
            'stderr': 'test_error'
        }
        mock_context = {
            'orquesta': {
                'task_name': 'python_error'
            }
        }
        test_execution = mock.Mock(id='123', context=mock_context, result=test_error_result)
        test_error_result_2 = {
            'result': {
                'details': {
                    'result_set': [{
                        'value': {'_error': {'msg': 'test_error'}}
                    }]
                }
            }
        }
        mock_context_2 = {
            'orquesta': {
                'task_name': 'bolt_error'
            }
        }
        test_execution_2 = mock.Mock(id='456', context=mock_context_2, result=test_error_result_2)
        test_error_result_3 = {
            'errors': [{'message': 'test_error'}]
        }
        mock_context_3 = {
            'orquesta': {
                'task_name': 'jinja_error'
            }
        }
        test_execution_3 = mock.Mock(id='789', context=mock_context_3, result=test_error_result_3)
        action.child_error = [test_execution, test_execution_2, test_execution_3]
        action.parent_error = None
        result = action.format_error(html_tags)
        self.assertEqual(result, expected_result)

    def test_format_error_child_returns(self):
        action = self.get_action_instance({})
        html_tags = False
        expected_result = ("Error task: python_error\nError execution ID: 123\n"
                           "Error message: test_error\nError task: bolt_error\n"
                           "Error execution ID: 456\nError message: test_error\n"
                           "Error task: jinja_error\nError execution ID: 789\n"
                           "Error message: test_error\n")
        test_error_result = {
            'result': 'None',
            'stderr': 'test_error'
        }
        mock_context = {
            'orquesta': {
                'task_name': 'python_error'
            }
        }
        test_execution = mock.Mock(id='123', context=mock_context, result=test_error_result)
        test_error_result_2 = {
            'result': {
                'details': {
                    'result_set': [{
                        'value': {'_error': {'msg': 'test_error'}}
                    }]
                }
            }
        }
        mock_context_2 = {
            'orquesta': {
                'task_name': 'bolt_error'
            }
        }
        test_execution_2 = mock.Mock(id='456', context=mock_context_2, result=test_error_result_2)
        test_error_result_3 = {
            'errors': [{'message': 'test_error'}]
        }
        mock_context_3 = {
            'orquesta': {
                'task_name': 'jinja_error'
            }
        }
        test_execution_3 = mock.Mock(id='789', context=mock_context_3, result=test_error_result_3)
        action.child_error = [test_execution, test_execution_2, test_execution_3]
        action.parent_error = None
        result = action.format_error(html_tags)
        self.assertEqual(result, expected_result)

    def test_get_error_string_html(self):
        action = self.get_action_instance({})
        html_tags = True
        test_err_context = "python_error"
        test_err_id = "1234"
        test_err_message = "test_error"

        expected_return = ("Error task: python_error<br>"
                           "Error execution ID: 1234<br>"
                           "Error message: test_error<br>")

        result = action.get_error_string(html_tags,
                                         test_err_context,
                                         test_err_id,
                                         test_err_message)

        self.assertEqual(result, expected_return)

    def test_get_error_string_returns(self):
        action = self.get_action_instance({})
        html_tags = False
        test_err_context = "python_error"
        test_err_id = "1234"
        test_err_message = "test_error"

        expected_return = ("Error task: python_error\n"
                           "Error execution ID: 1234\n"
                           "Error message: test_error\n")

        result = action.get_error_string(html_tags,
                                         test_err_context,
                                         test_err_id,
                                         test_err_message)

        self.assertEqual(result, expected_return)

    def test_format_error_strings(self):
        action = self.get_action_instance({})
        test_error = "testing\\\\nerror: test1"
        expected_return = "testing<br>error: test1"
        result_value = action.format_error_strings(test_error)
        self.assertEqual(result_value, expected_return)

    def test_format_error_ansi_strings(self):
        action = self.get_action_instance({})
        test_error = "\x1b[1;32mtesting\\\\nerror testing 0\x1b[0m"
        expected_return = "testing<br>error testing 0"
        result_value = action.format_error_strings(test_error)
        self.assertEqual(result_value, expected_return)

    def test_get_error_message_custom(self):
        action = self.get_action_instance({})
        expected_result = 'test_error'
        test_error_result = {
            'output': {'error': expected_result}
        }
        result = action.get_error_message(test_error_result)
        self.assertEqual(result, expected_result)

    def test_get_error_message_jinja(self):
        action = self.get_action_instance({})
        expected_result = 'test_error'
        test_error_result = {
            'errors': [{'message': expected_result}]
        }
        result = action.get_error_message(test_error_result)
        self.assertEqual(result, expected_result)

    def test_get_error_message_bolt_result(self):
        action = self.get_action_instance({})
        expected_result = 'test_error'
        test_error_result = {
            'result': expected_result
        }
        result = action.get_error_message(test_error_result)
        self.assertEqual(result, expected_result)

    def test_get_error_message_bolt_result_stderr(self):
        action = self.get_action_instance({})
        expected_result = 'test_error'
        test_error_result = {
            'result': {'stderr': expected_result}
        }
        result = action.get_error_message(test_error_result)
        self.assertEqual(result, expected_result)

    def test_get_error_message_bolt_result_details(self):
        action = self.get_action_instance({})
        expected_result = 'test_error'
        test_error_result = {
            'result': {
                'details': {
                    'result_set': [{
                        'value': {'_error': {'msg': expected_result}}
                    }]
                }
            }
        }
        result = action.get_error_message(test_error_result)
        self.assertEqual(result, expected_result)

    def test_get_error_message_python(self):
        action = self.get_action_instance({})
        expected_result = 'test_error'
        test_error_result = {
            'stderr': expected_result
        }
        result = action.get_error_message(test_error_result)
        self.assertEqual(result, expected_result)

    def test_get_error_message_python_empty_string(self):
        action = self.get_action_instance({})
        expected_result = 'test_error'
        test_error_result = {
            'result': '',
            'stderr': expected_result
        }
        result = action.get_error_message(test_error_result)
        self.assertEqual(result, expected_result)

    def test_get_error_message_python_none(self):
        action = self.get_action_instance({})
        expected_result = 'test_error'
        test_error_result = {
            'result': None,
            'stderr': expected_result
        }
        result = action.get_error_message(test_error_result)
        self.assertEqual(result, expected_result)

    def test_get_error_message_python_none_string(self):
        action = self.get_action_instance({})
        expected_result = 'test_error'
        test_error_result = {
            'result': 'None',
            'stderr': expected_result
        }
        result = action.get_error_message(test_error_result)
        self.assertEqual(result, expected_result)
