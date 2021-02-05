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
import six
import st2client
import st2client.commands.action
import st2client.models
from st2client.client import Client
from lib.base_action import BaseAction


QUEUED_STATUSES = [
    st2client.commands.action.LIVEACTION_STATUS_REQUESTED,
    st2client.commands.action.LIVEACTION_STATUS_SCHEDULED,
    st2client.commands.action.LIVEACTION_STATUS_DELAYED,
]

PROGRESS_STATUSES = [
    st2client.commands.action.LIVEACTION_STATUS_PAUSING,
    st2client.commands.action.LIVEACTION_STATUS_PAUSED,
    st2client.commands.action.LIVEACTION_STATUS_RESUMING,
    st2client.commands.action.LIVEACTION_STATUS_RUNNING
]

COMPLETED_STATUSES = [
    st2client.commands.action.LIVEACTION_STATUS_SUCCEEDED
]

ERRORED_STATUSES = [
    st2client.commands.action.LIVEACTION_STATUS_FAILED,
    st2client.commands.action.LIVEACTION_STATUS_TIMED_OUT,
    st2client.commands.action.LIVEACTION_STATUS_ABANDONED,
    st2client.commands.action.LIVEACTION_STATUS_CANCELED
]

STACKSTORM_STATUSES = {
    'queued': QUEUED_STATUSES,
    'running': PROGRESS_STATUSES,
    'succeeded': COMPLETED_STATUSES,
    'failed': ERRORED_STATUSES
}

COMPLETED_STATUSES = [
    st2client.commands.action.LIVEACTION_STATUS_SUCCEEDED
]


class ExecutionFindResults(BaseAction):

    def __init__(self, config):
        """Creates a new BaseAction given a StackStorm config object (kwargs works too)
        :param config: StackStorm configuration object for the pack
        :returns: a new BaseAction
        """
        super(ExecutionFindResults, self).__init__(config)
        self.st2_exe_id = ""

    def check_status(self, st2_execution):

        st2_status = 'unknown'
        for k, v in six.iteritems(STACKSTORM_STATUSES):
            if st2_execution and st2_execution.status in v:
                st2_status = k

        # st2_execution_comments comments needs to be defaulted to an empty string
        # else there is a trigger error saying that the value does not exists.
        execution_status = {
            'st2_execution_id': self.st2_exe_id,
            'st2_execution_status': st2_status,
            'st2_execution_comments': ""
        }

        self.find_error_execution(st2_execution, self.provision_skip_list)

        if st2_status == 'failed':
            execution_status['st2_execution_comments'] = self.format_error(html_tags=False)
        elif st2_status == 'unknown':
            execution_status['st2_execution_comments'] = ("Could not find execution_id "
                                                        "in database")

        return execution_status

    def run(self, **kwargs):

        self.provision_skip_list = kwargs['provision_skip_list']
        self.st2_exe_id = kwargs['st2_exe_id']

        st2_execution = self.st2_client_initialize(self.st2_exe_id)

        return self.check_status(st2_execution)