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

SERVICENOW_STATUSES = {
    'queued': QUEUED_STATUSES,
    'running': PROGRESS_STATUSES,
    'succeeded': COMPLETED_STATUSES,
    'failed': ERRORED_STATUSES
}

PROVISION_SKIP_LIST = [
    'vm_delete',
    'provision_cleanup',
    'provision_cleanup_exec'
]

COMPLETED_STATUSES = [
    st2client.commands.action.LIVEACTION_STATUS_SUCCEEDED
]


class ErrorsProvisionErrors(BaseAction):

    def __init__(self, config):
        """Creates a new BaseAction given a StackStorm config object (kwargs works too)
        :param config: StackStorm configuration object for the pack
        :returns: a new BaseAction
        """
        super(ErrorsProvisionErrors, self).__init__(config)
        self.st2_exe_id = ""

    def check_status(self, st2_execution):

        st2_status = 'unknown'
        for k, v in six.iteritems(SERVICENOW_STATUSES):
            if st2_execution and st2_execution.status in v:
                st2_status = k

        # st2_execution_comments comments needs to be defaulted to an empty string
        # else there is a trigger error saying that the value does not exists.
        execution_status = {
            'st2_execution_id': self.st2_exe_id,
            'st2_execution_status': st2_status,
            'st2_execution_comments': ""
        }

        if st2_status == 'failed':
            execution_status['st2_execution_comments'] = self.get_st2_error(st2_execution)
        elif st2_status == 'unknown':
            execution_status['st2_execution_comments'] = ("Could not find execution_id "
                                                        "in database")

        return execution_status

    def get_st2_error(self, st2_execution):
        """ Checks the ST2 object for any errors that can be found
        if an error can not be found "Unknown" is returned so that
        more investigation can be done.
        Returns: string
        """
        st2_result = st2_execution.result
        error_return = 'Unknown'
        task_list = st2_result.get('task_list')

        if task_list:
            error_task = next((t for t in task_list if t['status'].lower() == 'error'), None)
            if error_task:
                error_return = error_task.get('err_reason', 'Unknown')

            if error_return == 'Unknown':
                error_return = self.check_for_task_error(st2_execution)
        else:
            error_return = self.combine_error_strings(st2_result, 'traceback', 'error')

        # Make sure that string escapes are proper for servicenow formatting
        while "\\n" in error_return:
            # We need to encode first for python3 to decode byte string
            error_return_encoded = error_return.encode()
            error_return = error_return_encoded.decode('unicode_escape')

        return error_return

    def check_for_task_error(self, st2_execution):
        """ Looks at each task in the provision list to try to find one
        that errored.
        Returns: string
        """
        error_return = 'Unknown'

        # Reverse provision list so that we get the latest list of tasks to traverse
        # Task list in result should already be in reverse order
        error_task = self.get_task_error(st2_execution)

        if error_task:
            # Get any information that the task has in the STDOUT and STDERR
            error_return = self.combine_error_strings(error_task.result, 'stdout', 'stderr')

        return error_return

    def get_task_error(self, st2_execution):
        """Recursively go through all children tasks that are not appart of the
        clean up tasks to get the task that has error if one exists and return
        it.
        Returns:
            ST2 execution object or None
        """
        if hasattr(st2_execution, 'children'):
            for st2_id in st2_execution.children:
                execution = self.st2_client.liveactions.get_by_id(st2_id)

                # Don't look at cleanup tasks as they will most likey contain errors
                # depending upon how far the provision got.
                if execution.action['name'] in PROVISION_SKIP_LIST:
                    continue

                error_task = self.get_task_error(execution)
                if error_task:
                    return error_task
        else:
            if st2_execution.action['name'] == "provision_check_complete":
                # This will have failures until it succeeds. Adding in this check to look
                # specifically for a timeout status
                if st2_execution.status == st2client.commands.action.LIVEACTION_STATUS_TIMED_OUT:
                    return st2_execution
                else:
                    return None
            elif st2_execution.status in ERRORED_STATUSES:
                return st2_execution
            else:
                return None

    def combine_error_strings(self, error_object, first_key, second_key):
        """ Check if the keys exist in the object and if they do they
        add them to the error string and return it.
        Returns: string
        """
        error_return = ""

        first_entry = error_object.get(first_key)
        second_entry = error_object.get(second_key)

        if first_entry:
            error_return += "{0}: {1}".format(first_key, first_entry)

        if error_return:
            error_return += "\n"

        if second_entry:
            error_return += "{0}: {1}".format(second_key, second_entry)

        if not error_return:
            error_return = 'Unknown'

        return error_return

    def run(self, **kwargs):

        self.st2_exe_id = kwargs['st2_exe_id']
        self.st2_fqdn = socket.getfqdn()

        st2_url = "https://{}/".format(self.st2_fqdn)
        self.st2_client = Client(base_url=st2_url)
        st2_execution = self.st2_client.liveactions.get_by_id(self.st2_exe_id)

        return self.check_status(st2_execution)