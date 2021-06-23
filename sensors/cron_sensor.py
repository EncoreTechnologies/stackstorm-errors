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
from st2reactor.sensor.base import PollingSensor
import st2client
import st2client.commands.action
import st2client.models
from st2client.client import Client
import socket
import datetime
from crontab import CronTab
import ast

# Note: These modules are manipulated during the runtime so we can't detect all the
# properties during static analysis
from dateutil.parser import parse  # pylint: disable=import-error
import pytz  # pylint: disable=import-error

__all__ = [
    'CronSensor'
]

ERRORED_STATUSES = [
    st2client.commands.action.LIVEACTION_STATUS_FAILED,
    st2client.commands.action.LIVEACTION_STATUS_TIMED_OUT,
    st2client.commands.action.LIVEACTION_STATUS_ABANDONED,
    st2client.commands.action.LIVEACTION_STATUS_CANCELED
]

PROGRESS_STATUSES = [
    st2client.commands.action.LIVEACTION_STATUS_REQUESTED,
    st2client.commands.action.LIVEACTION_STATUS_SCHEDULED,
    st2client.commands.action.LIVEACTION_STATUS_DELAYED,
    st2client.commands.action.LIVEACTION_STATUS_PAUSING,
    st2client.commands.action.LIVEACTION_STATUS_PAUSED,
    st2client.commands.action.LIVEACTION_STATUS_RESUMING,
    st2client.commands.action.LIVEACTION_STATUS_RUNNING
]

COMPLETED_STATUSES = [
    st2client.commands.action.LIVEACTION_STATUS_SUCCEEDED
]

STACKSTORM_TO_CRONTAB_DAYS = {
    # Stackstorm Cron days => Crontab days
    0: 1,
    1: 2,
    2: 3,
    3: 4,
    4: 5,
    5: 6,
    6: 0,
}


class CronSensor(PollingSensor):
    def __init__(self, sensor_service, config=None, poll_interval=None):
        super(CronSensor, self).__init__(sensor_service=sensor_service,
                                         config=config,
                                         poll_interval=poll_interval)
        self._logger = self._sensor_service.get_logger(__name__)
        self.trigger_ref = "errors.error_cron_event"

    def setup(self):
        self.st2_fqdn = socket.getfqdn()
        st2_url = "https://{}/".format(self.st2_fqdn)
        self.st2_client = Client(base_url=st2_url)

        self.kv_sensor_name = self._config['error_cron_event']['datastore_key']

    def poll(self):
        # Get the current datetime with a timezone
        utc_date_time = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)

        rules = self.get_cron_rules()

        # Get information from key value store if it doesn't exist
        # then initialize as empty dictionary
        self.kv_enforcements = self._sensor_service.get_value(name=self.kv_sensor_name)
        if not self.kv_enforcements:
            self.kv_enforcements = {}

        # If the key does exist in the key value store then it will be returned
        # as a string value so we need to convert it.
        if not isinstance(self.kv_enforcements, dict):
            self.kv_enforcements = ast.literal_eval(self.kv_enforcements)

        self._logger.info("Current problem rules: {0}".format(self.kv_enforcements))

        for rule in rules:
            cron_time = CronTab(self.convert_to_crontab(rule.trigger['parameters']))

            # Gets the previous run time in seconds
            previous_cron_s = cron_time.previous(now=utc_date_time, delta=False)
            next_cron_s = cron_time.next(now=utc_date_time, delta=False)

            # converts from seconds to a useable datetime format
            previous_cron_stamp = datetime.datetime.utcfromtimestamp(previous_cron_s)
            next_cron_stamp = datetime.datetime.utcfromtimestamp(next_cron_s)

            # Adds the timezone information to the time stamp
            previous_cron_dt = previous_cron_stamp.replace(tzinfo=pytz.UTC)
            next_cron_dt = next_cron_stamp.replace(tzinfo=pytz.UTC)

            enforcements = self.st2_client.ruleenforcements.query(rule_ref=rule.ref)
            if len(enforcements) > 0:
                self._logger.info("Checking enforcements for rule: {0}".format(rule.ref))
                result = self.check_enforcements(enforcements, previous_cron_dt, next_cron_dt)

                if result:
                    self.delete_from_kv(rule.ref)
            else:
                st2_comments = "Cron job is not running and no enforcements can be found"
                self.dispatch_trigger(st2_rule_name=rule.ref,
                                      st2_server=self.st2_fqdn,
                                      st2_comments=st2_comments,
                                      st2_state="open")

        self._sensor_service.set_value(name=self.kv_sensor_name, value=self.kv_enforcements)

    def check_enforcements(self, enforcements, previous_cron, next_cron):
        """ Checks all the enforments to find if the cron was executed and to
        get the status of the execution if one can be found
        """
        for enforcement in enforcements:
            # Parse the enforcement enforced time to be in datetime format for comparison
            # We need to drop the microseconds from the datetime format for the comparison
            # to be accurate
            enforced_at = parse(enforcement.enforced_at).replace(microsecond=0)

            # Creating a buffer of one run time
            cron_delta = next_cron - previous_cron
            cron_low_buffer = previous_cron - cron_delta

            if cron_low_buffer <= enforced_at <= next_cron:
                # If the rule logic fails then no execution_id exists in the rule enforcement
                if hasattr(enforcement, 'execution_id'):
                    st2_execution = self.st2_client.liveactions.get_by_id(enforcement.execution_id)
                    if st2_execution.status in PROGRESS_STATUSES:
                        self._logger.info("Currently running execution. Will check next run")
                        return False
                    elif st2_execution.status in ERRORED_STATUSES:
                        self.dispatch_trigger(st2_rule_name=enforcement.rule['ref'],
                                              st2_server=self.st2_fqdn,
                                              st2_execution_id=enforcement.execution_id,
                                              st2_comments="Cronjob execution failed",
                                              st2_enforcement_id=enforcement.id)
                        return False
                    else:
                        if enforcement.rule['ref'] in self.kv_enforcements:
                            self.dispatch_trigger(st2_rule_name=enforcement.rule['ref'],
                                                  st2_server=self.st2_fqdn,
                                                  st2_execution_id=enforcement.execution_id,
                                                  st2_comments="Cronjob ran successfully",
                                                  st2_enforcement_id=enforcement.id,
                                                  st2_state="success")
                        return True
                else:
                    rule_enforcement = self.st2_client.ruleenforcements.get_by_id(enforcement.id)
                    # When rule failures have jinja expressions in it those have to be escaped so
                    # mistral does not attempt to render the jinja expression as a template.
                    rule_fail_reason = rule_enforcement.failure_reason
                    # W605 = invalid escape sequence flake8 error that we want to ignore
                    escape_beggining_bracket = \
                        rule_fail_reason.replace('{{', '\{\{')  # noqa: W605
                    escape_ending_bracket = \
                        escape_beggining_bracket.replace('}}', '\}\}')  # noqa: W605

                    self.dispatch_trigger(st2_rule_name=enforcement.rule['ref'],
                                          st2_server=self.st2_fqdn,
                                          st2_comments=escape_ending_bracket,
                                          st2_enforcement_id=enforcement.id)
                    return False

        # If a enforcement could not be found within the time this run to say that the
        # Job is not running. This solves the condition where the st2 config was changed
        # and cron jobs stopped running.
        self.dispatch_trigger(st2_rule_name=enforcements[0].rule['ref'],
                              st2_server=self.st2_fqdn,
                              st2_comments="Cron job did not run",
                              st2_state="open")
        return False

    def dispatch_trigger(self,
                         st2_rule_name,
                         st2_server,
                         st2_execution_id="",
                         st2_comments="",
                         st2_enforcement_id=None,
                         st2_state="error"):
        trigger_payload = {
            'st2_rule_name': st2_rule_name,
            'st2_server': st2_server,
            'st2_execution_id': st2_execution_id,
            'st2_comments': st2_comments,
            'st2_state': st2_state
        }
        if st2_state == "success":
            self._sensor_service.dispatch(trigger=self.trigger_ref, payload=trigger_payload)
            return True

        if self.check_before_dispatch(st2_rule_name, st2_enforcement_id):
            self._logger.info("Sending trigger with payload: {0}".format(trigger_payload))

            self._sensor_service.dispatch(trigger=self.trigger_ref, payload=trigger_payload)

            if st2_enforcement_id:
                self.kv_enforcements[st2_rule_name] = st2_enforcement_id
            else:
                self.kv_enforcements[st2_rule_name] = "error without enforcement id"

        else:
            self._logger.info("Already dispatched trigger. Waiting till another enforcement before"
                             " dispatching another trigger.")

        return True

    def check_before_dispatch(self, st2_rule_name, st2_enforcement_id):
        """ Checks the key value object to see if it already exists
        If it does then we return false saying that it does not need to
        Sent to servicenow again.
        """
        if st2_rule_name in self.kv_enforcements:
            if st2_enforcement_id and st2_enforcement_id == self.kv_enforcements[st2_rule_name]:
                return False
            elif self.kv_enforcements[st2_rule_name] == "error without enforcement id":
                return False

        return True

    def delete_from_kv(self, rule_name):
        if rule_name in self.kv_enforcements:
            del self.kv_enforcements[rule_name]

        return self.kv_enforcements

    def get_cron_rules(self):
        """ Gets all the enabled rules that are of type 'core.st2.CronTimer'
        """
        enabled_rules = self.st2_client.rules.query(enabled=True)

        cron_rules = []
        for rule in enabled_rules:
            if rule.trigger['type'] == "core.st2.CronTimer":
                cron_rules.append(rule)

        return cron_rules

    def convert_to_crontab(self, st2_cron):
        """ Converts Stackstorm cron information to standard crontab
        If day of the week is an integer covert it to the correct
        integer as stackstorm starts the week on monday where
        cron tab starts on Sunday
        https://docs.stackstorm.com/rules.html#core-st2-crontimer
        """
        day_of_week = st2_cron.get('day_of_week', '*')
        if isinstance(day_of_week, int):
            day_of_week = STACKSTORM_TO_CRONTAB_DAYS[day_of_week]

        cron_tab = [
            str(st2_cron.get('second', '*')),
            str(st2_cron.get('minute', '*')),
            str(st2_cron.get('hour', '*')),
            str(st2_cron.get('day', '*')),
            str(st2_cron.get('month', '*')),
            str(day_of_week),
            str(st2_cron.get('year', '*'))
        ]

        return " ".join(cron_tab)

    def cleanup(self):
        pass

    def add_trigger(self, trigger):
        pass

    def update_trigger(self, trigger):
        pass

    def remove_trigger(self, trigger):
        pass
