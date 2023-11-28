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


class GetFormattedError(BaseAction):

    def __init__(self, config):
        """Creates a new BaseAction given a StackStorm config object (kwargs works too)
        :param config: StackStorm configuration object for the pack
        :returns: a new BaseAction
        """
        super(GetFormattedError, self).__init__(config)

    def run(self, **kwargs):

        st2_exe_id = kwargs['st2_exe_id']
        html_tags = kwargs['html_tags']
        ignored_error_tasks = kwargs['ignored_error_tasks']
        errors = ""

        parent_execution = self.st2_client_initialize(st2_exe_id)

        self.find_error_execution(parent_execution, ignored_error_tasks)

        if len(self.child_error) == 0:
            self.parent_errors.append(parent_execution)
            for exe in self.parent_errors:
                if exe.status == 'failed' or exe.status == 'timeout':
                    if html_tags:
                        errors += self.format_error_strings(self.get_error_message(exe.result, exe))
                    else:
                        errors += self.get_error_message(exe.result, exe)
            return errors

        return self.format_error(html_tags)
