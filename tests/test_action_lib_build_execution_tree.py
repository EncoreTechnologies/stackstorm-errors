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
from build_execution_tree import BuildExecutionTree
from lib.base_action import BaseAction
from st2common.runners.base_action import Action
import mock

__all__ = [
    'TestBuildExecutionTree'
]


class TestBuildExecutionTree(ErrorsBaseActionTestCase):
    __test__ = True
    action_cls = BuildExecutionTree

    def test_init(self):
        action = self.get_action_instance({})
        self.assertIsInstance(action, BuildExecutionTree)
        self.assertIsInstance(action, BaseAction)
        self.assertIsInstance(action, Action)

    def test_build_execution_tree(self):
        action = self.get_action_instance({})
        action.task_list = []
        mock_context = {
            'orquesta': {
                'task_name': 'vsphere_check'
            }
        }
        test_execution = mock.Mock(children=[], context=mock_context, status='succeeded')
        mock_client = mock.Mock()
        mock_client.executions.get_by_id.return_value = test_execution
        action.st2_client = mock_client

        mock_parent_execution = '1234'

        expected_result = [
            {
                'status': "succeeded",
                'name': "<pre><code>   +> vsphere_check</pre></code>"
            }
        ]
        action.get_execution_tree(mock_parent_execution, '   ')
        self.assertEqual(action.task_list, expected_result)

    @mock.patch("build_execution_tree.BuildExecutionTree.get_execution_tree")
    @mock.patch("lib.base_action.BaseAction.st2_client_initialize")
    def test_run(self, mock_st2_client_initialize, mock_get_execution_tree):
        action = self.get_action_instance({})
        kwargs_dict = {'st2_exe_id': '1234'}

        mock_execution = mock.Mock(action={'ref': 'test_ref'}, status='succeeded')
        mock_st2_client_initialize.return_value = mock_execution

        mock_get_execution_tree.return_value = [
            {
                'status': "succeeded",
                'name': "<pre><code>   +> vsphere_check</pre></code>"
            }
        ]

        expected_return = [
            {
                'name': "test_ref",
                'status': "succeeded",
                'name': "<pre><code>   +> vsphere_check</pre></code>",
                'status': "succeeded"
            }
        ]

        result = action.run(**kwargs_dict)
        self.assertEqual(result, expected_return)
