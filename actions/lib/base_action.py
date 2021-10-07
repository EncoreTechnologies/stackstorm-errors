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

import socket
import re
from six import string_types
from st2common.runners.base_action import Action
from st2client.client import Client


class BaseAction(Action):

    def __init__(self, config):
        """Creates a new BaseAction given a StackStorm config object (kwargs works too)
        :param config: StackStorm configuration object for the pack
        :returns: a new BaseAction
        """
        super(BaseAction, self).__init__(config)
        self.child_error = []
        self.parent_output = []
        self.errors_as_string = ""
        self.parent_errors = []

    def st2_client_initialize(self, st2_exe_id):
        st2_fqdn = socket.getfqdn()
        st2_url = "https://{}/".format(st2_fqdn)
        self.st2_client = Client(base_url=st2_url)

        vm_execution = self.st2_client.executions.get_by_id(st2_exe_id)

        return vm_execution

    def find_error_execution(self, parent_execution, ignored_error_tasks):
        if hasattr(parent_execution, 'children'):
            for m in parent_execution.children:
                self.find_error_execution(str(m), ignored_error_tasks)
        else:
            execution = parent_execution
            if isinstance(parent_execution, string_types):
                st2_executions = self.st2_client.executions
                execution = st2_executions.get_by_id(parent_execution)
            if (str(execution.status) == "failed" or str(execution.status) == "timeout"):
                if ("orquesta" in execution.context and execution.context['orquesta']['task_name']
                        in ignored_error_tasks):
                    pass
                else:
                    self.parent_errors.append(execution)
                    execution_result = execution.result
                    if self.check_custom_errors(execution_result, execution):
                        return None
                    self.parent_error = execution
                    if hasattr(execution, 'children'):
                        for c in execution.children:
                            self.find_error_execution(c, ignored_error_tasks)
                    else:
                        self.child_error.append(execution)

    def check_custom_errors(self, execution_result, execution):
        if 'output' in execution_result and execution_result['output']:
            if execution_result.get('output', {}).get('error'):
                self.parent_error = execution
                parent_errors = execution_result['output']['error']
                if isinstance(parent_errors, string_types):
                    self.errors_as_string = parent_errors
                    return True
                for error in parent_errors:
                    for errors in error:
                        self.parent_output.append(error['error'])
                self.errors_as_string = '\n'.join(self.parent_output)
                return True
        return False

    def format_error(self, html_tags):
        err_string = ""

        if self.child_error:
            for error in self.child_error:
                if html_tags:
                    err_message = self.format_error_strings(self.get_error_message(error.result))
                else:
                    err_message = self.get_error_message(error.result)
                    err_message = err_message

                if "orquesta" in error.context:
                    err_string += self.get_error_string(html_tags,
                                                        error.context['orquesta']['task_name'],
                                                        error.id,
                                                        err_message)
                else:
                    err_string += self.get_error_message(error.result)
        else:
            if html_tags:
                error_result = self.parent_error.result
                if self.errors_as_string:
                    parent_error = self.errors_as_string
                else:
                    parent_error = self.get_error_message(error_result)
                err_message = self.format_error_strings(parent_error)
                err_string += self.get_error_string(html_tags,
                                                    self.parent_error
                                                    .context['orquesta']['task_name'],
                                                    self.parent_error.id,
                                                    err_message)
            else:
                if self.errors_as_string:
                    parent_error = self.errors_as_string
                else:
                    parent_error = self.get_error_message(self.parent_error.result)
                    parent_error = parent_error

                err_string += self.get_error_string(html_tags,
                                                    self.parent_error
                                                    .context['orquesta']['task_name'],
                                                    self.parent_error.id,
                                                    parent_error)

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
            if 'error' in error_result['output'] and error_result['output']['error'] is not None:
                return error_result['output']['error']

        # Jinja syntax errors
        if 'errors' in error_result:
            error = error_result['errors'][0]['message']
            return error.replace("{{", '\\{\\{').replace("}}", '\\}\\}')

        # StackStorm errors (ex. timeouts)
        if 'error' in error_result:
            return error_result['error']

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
        raise RuntimeError("run() not implemented")
