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

from lib.base_action import BaseAction


class BuildExecutionTree(BaseAction):

    def __init__(self, config):
        """Creates a new BaseAction given a StackStorm config object (kwargs works too)
        :param config: StackStorm configuration object for the pack
        :returns: a new BaseAction
        """
        super(BuildExecutionTree, self).__init__(config)

    def get_execution_tree(self, parent_execution, delimeter):
        if hasattr(parent_execution, 'children'):
            for m in parent_execution.children:
                self.get_execution_tree(m, delimeter)
        else:
            st2_executions = self.st2_client.executions  # pylint: disable=no-member
            execution = st2_executions.get_by_id(parent_execution)
            has_child = hasattr(execution, 'children')
            symbol = '+> ' if has_child else '   '
            task_name = delimeter + symbol + execution.context['orquesta']['task_name']
            task_dict = {
                'name': "<pre><code>{0}</pre></code>".format(task_name),
                'status': execution.status
            }
            self.task_list.append(task_dict)  # pylint: disable=no-member
            if has_child:
                for c in execution.children:
                    self.get_execution_tree(c, delimeter + '   ')

        return self.task_list

    def run(self, st2_exe_id):

        parent_execution = self.st2_client_initialize(st2_exe_id)
        self.task_list = []
        delimeter = '   '

        parent_task_name = '+> ' + parent_execution.action['ref']
        self.task_list.append({'name': parent_task_name,
                               'status': parent_execution.status})

        return self.get_execution_tree(parent_execution, delimeter)
