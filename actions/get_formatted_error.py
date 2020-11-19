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

import re
from six import string_types
from lib.base_action import BaseAction


IGNORED_ERROR_TASKS = [
    'send_error_email',
    'provision_cleanup_exec'
]


class GetFormattedError(BaseAction):

    def __init__(self, config):
        """Creates a new BaseAction given a StackStorm config object (kwargs works too)
        :param config: StackStorm configuration object for the pack
        :returns: a new BaseAction
        """
        super(GetFormattedError, self).__init__(config)
        self.child_error = []

    def find_error_execution(self, parent_execution, ignored_error_tasks):
        if hasattr(parent_execution, 'children'):
            for m in parent_execution.children:
                self.find_error_execution(m, ignored_error_tasks)
        else:
            st2_executions = self.st2_client.executions
            execution = st2_executions.get_by_id(parent_execution)
            if (execution.status == "failed" and
               execution.context['orquesta']['task_name'] not in ignored_error_tasks):
                self.parent_error = execution
                if hasattr(execution, 'children'):
                    for c in execution.children:
                        self.find_error_execution(c, ignored_error_tasks)
                else:
                    self.child_error.append(execution)

    def format_error(self, html_tags):
        err_string = ""

        if self.child_error:
            for error in self.child_error:
                if html_tags:
                    err_message = self.format_error_strings(self.get_error_message(error.result))
                else:
                    err_message = self.get_error_message(error.result)

                err_string += self.get_error_string(html_tags,
                                                    error.context['orquesta']['task_name'],
                                                    error.id,
                                                    err_message)
        else:
            if html_tags:
                error_result = self.parent_error.result
                parent_error = self.get_error_message(error_result)
                err_message = self.format_error_strings(parent_error)
            else:
                parent_error = self.get_error_message(self.parent_error.result)

            err_string += self.get_error_string(html_tags,
                                                self.parent_error.context['orquesta']['task_name'],
                                                self.parent_error.id,
                                                err_message)

        return err_string

    def get_error_string(self, html_tags, err_context, err_id, err_message):
        if html_tags:
            return ("Error task: {0}<br>Error execution ID: {1}<br>Error message: {2}"
                    "<br>".format(err_context, err_id, err_message))
        else:
            return ("Error task: {0}\nError execution ID: {1}\nError message: {2}"
                    "\n".format(err_context, err_id, err_message))


    def format_error_strings(self, error_string):
        """ formats error strings by dropping extra string escapes
        and drops the ansi escapes. Then we convert the new lines into
        <br> so that new lines appear correctly.
        """
        # ansi escape sequence
        ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')

        while "\\n" in error_string:
            # We need to encode first for python3 to decode byte string
            error_string_encoded = error_string.encode()
            error_string = error_string_encoded.decode('unicode_escape')

        error_string = ansi_escape.sub('', error_string)

        error_string = error_string.replace('\n', '<br>')

        return error_string

    def get_error_message(self, error_result):
        # Custom Error Messages returned from workflow outputs
        if 'output' in error_result and error_result['output']:
            if 'error' in error_result['output']:
                return error_result['output']['error']

        # Jinja syntax errors
        if 'errors' in error_result:
            return error_result['errors'][0]['message']

        # Bolt plans (https://github.com/StackStorm-Exchange/stackstorm-bolt)
        if ('result' in error_result and
           error_result['result'] and
           error_result['result'] != 'None'):
            if 'details' in error_result['result']:
                if 'result_set' in error_result['result']['details']:
                    result_set = error_result['result']['details']['result_set'][0]
                    return result_set['value']['_error']['msg']

            if isinstance(error_result['result'], string_types):
                return error_result['result']

            if 'stderr' in error_result['result']:
                return error_result['result']['stderr']

        # python actions
        # ex. (vsphere pack https://github.com/StackStorm-Exchange/stackstorm-vsphere)
        if 'stderr' in error_result:
            return error_result['stderr']

        return "Could not retrieve error message"

    def run(self, **kwargs):

        st2_exe_id = kwargs['st2_exe_id']
        html_tags = kwargs['html_tags']
        ignored_error_tasks = kwargs['ignored_error_tasks']

        parent_execution = self.st2_client_initialize(st2_exe_id)

        self.find_error_execution(parent_execution, ignored_error_tasks)

        return self.format_error(html_tags)
