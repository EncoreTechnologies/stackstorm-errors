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
from st2tests.base import BaseSensorTestCase

from cron_sensor import CronSensor
from st2reactor.sensor.base import PollingSensor
import mock
import datetime
import pytz
import yaml
from freezegun import freeze_time

__all__ = [
    'CronSensorTestCase'
]


class CronSensorTestCase(BaseSensorTestCase):
    __test__ = True
    sensor_cls = CronSensor

    def test_init(self):
        sensor = self.get_sensor_instance()
        self.assertIsInstance(sensor, CronSensor)
        self.assertIsInstance(sensor, PollingSensor)

    @mock.patch('cron_sensor.Client')
    @mock.patch('cron_sensor.socket')
    def test_setup(self, mock_socket, mock_client):
        config = yaml.safe_load(self.get_fixture_content('config_good.yaml'))
        sensor = self.get_sensor_instance(config)
        mock_socket.getfqdn.return_value = "st2_test"
        mock_client.return_value = "Client"
        sensor.setup()

    @freeze_time("2018-10-26 01:00")
    def test_poll(self):
        sensor = self.get_sensor_instance()
        sensor.st2_fqdn = 'st2_test'
        sensor.kv_sensor_name = 'test_sensor'
        sensor.kv_enforcements = {}

        trigger_attributes = {
            'type': "core.st2.CronTimer",
            'parameters': {
                'day_of_week': '*',
                'hour': 1,
                'minute': 0,
                'second': 0,
                'timezone': 'UTC'
            }
        }

        mock_rule = mock.Mock(ref='test_rule', trigger=trigger_attributes)
        mock_enforcement = mock.Mock(enforced_at='2018-10-26T01:00:00.01Z',
                                     execution_id='test_execution',
                                     rule={'ref': 'test_rule'})

        mock_st2_client = mock.MagicMock()
        mock_st2_client.rules.query.return_value = [mock_rule]
        mock_st2_client.ruleenforcements.query.return_value = [mock_enforcement]
        sensor.st2_client = mock_st2_client

        sensor.poll()

    @freeze_time("2018-10-26 01:00")
    def test_poll_no_enforcements(self):
        sensor = self.get_sensor_instance()
        sensor.st2_fqdn = 'st2_test'
        sensor.kv_sensor_name = 'test_sensor'
        sensor.kv_enforcements = {}

        trigger_attributes = {
            'type': "core.st2.CronTimer",
            'parameters': {
                'day_of_week': '*',
                'hour': 1,
                'minute': 0,
                'second': 0,
                'timezone': 'UTC'
            }
        }

        mock_rule = mock.Mock(ref='test_rule', trigger=trigger_attributes)

        mock_st2_client = mock.MagicMock()
        mock_st2_client.rules.query.return_value = [mock_rule]
        mock_st2_client.ruleenforcements.query.return_value = []
        sensor.st2_client = mock_st2_client

        trigger_payload = {
            'st2_rule_name': 'test_rule',
            'st2_server': 'st2_test',
            'st2_execution_id': '',
            'st2_comments': 'Cron job is not running and no enforcements can be found',
            'st2_state': 'error'
        }

        sensor.poll()
        self.assertTriggerDispatched(trigger='errors.error_cron_event',
                                     payload=trigger_payload)
        self.assertEqual(sensor.kv_enforcements, {'test_rule': 'error without enforcement id'})

    def test_check_enforcements_date_error(self):
        sensor = self.get_sensor_instance()
        sensor.st2_fqdn = 'st2_test'
        sensor.kv_enforcements = {}

        mock_enforcement = mock.Mock(id='test_id',
                                     enforced_at='2018-10-20T01:00:00.01Z',
                                     execution_id='test_execution',
                                     rule={'ref': 'test_rule'})

        test_dict = {
            'previous_cron': datetime.datetime(2018, 10, 26, 1, 0).replace(tzinfo=pytz.UTC),
            'next_cron': datetime.datetime(2018, 10, 27, 1, 0).replace(tzinfo=pytz.UTC),
            'enforcements': [mock_enforcement]
        }

        trigger_payload = {
            'st2_rule_name': 'test_rule',
            'st2_server': 'st2_test',
            'st2_execution_id': '',
            'st2_comments': 'Cron job did not run',
            'st2_state': 'error'
        }

        result_value = sensor.check_enforcements(**test_dict)
        self.assertEqual(result_value, False)
        self.assertTriggerDispatched(trigger='errors.error_cron_event',
                                     payload=trigger_payload)
        self.assertEqual(sensor.kv_enforcements, {'test_rule': 'error without enforcement id'})

    def test_check_enforcements_error(self):
        sensor = self.get_sensor_instance()
        sensor.st2_fqdn = 'st2_test'
        sensor.kv_enforcements = {}

        mock_enforcement = mock.Mock(id='test_id',
                                     enforced_at='2018-10-26T01:00:00.01Z',
                                     execution_id='test_execution',
                                     rule={'ref': 'test_rule'})
        mock_execution = mock.Mock(status='failed')

        mock_st2_client = mock.MagicMock()
        mock_st2_client.liveactions.get_by_id.return_value = mock_execution
        sensor.st2_client = mock_st2_client

        test_dict = {
            'previous_cron': datetime.datetime(2018, 10, 26, 1, 0).replace(tzinfo=pytz.UTC),
            'next_cron': datetime.datetime(2018, 10, 27, 1, 0).replace(tzinfo=pytz.UTC),
            'enforcements': [mock_enforcement]
        }

        trigger_payload = {
            'st2_rule_name': 'test_rule',
            'st2_server': 'st2_test',
            'st2_execution_id': 'test_execution',
            'st2_comments': 'Cronjob execution failed',
            'st2_state': 'error'
        }

        result_value = sensor.check_enforcements(**test_dict)
        self.assertEqual(result_value, False)
        self.assertTriggerDispatched(trigger='errors.error_cron_event',
                                     payload=trigger_payload)
        self.assertEqual(sensor.kv_enforcements, {'test_rule': 'test_id'})

    def test_check_enforcements_error_no_dispatch(self):
        sensor = self.get_sensor_instance()
        sensor.st2_fqdn = 'st2_test'
        sensor.kv_enforcements = {'test_rule': 'test_id'}

        mock_enforcement = mock.Mock(id='test_id',
                                     enforced_at='2018-10-26T01:00:00.01Z',
                                     execution_id='test_execution',
                                     rule={'ref': 'test_rule'})
        mock_execution = mock.Mock(status='failed')

        mock_st2_client = mock.MagicMock()
        mock_st2_client.liveactions.get_by_id.return_value = mock_execution
        sensor.st2_client = mock_st2_client

        test_dict = {
            'previous_cron': datetime.datetime(2018, 10, 26, 1, 0).replace(tzinfo=pytz.UTC),
            'next_cron': datetime.datetime(2018, 10, 27, 1, 0).replace(tzinfo=pytz.UTC),
            'enforcements': [mock_enforcement]
        }

        result_value = sensor.check_enforcements(**test_dict)
        self.assertEqual(result_value, False)
        self.assertEqual(sensor.kv_enforcements, {'test_rule': 'test_id'})

    def test_check_enforcements_error_running(self):
        sensor = self.get_sensor_instance()
        sensor.st2_fqdn = 'st2_test'
        sensor.kv_enforcements = {'test_rule': 'test_id'}

        mock_enforcement = mock.Mock(id='test_id',
                                     enforced_at='2018-10-26T01:00:00.01Z',
                                     execution_id='test_execution',
                                     rule={'ref': 'test_rule'})
        mock_execution = mock.Mock(status='running')

        mock_st2_client = mock.MagicMock()
        mock_st2_client.liveactions.get_by_id.return_value = mock_execution
        sensor.st2_client = mock_st2_client

        test_dict = {
            'previous_cron': datetime.datetime(2018, 10, 26, 1, 0).replace(tzinfo=pytz.UTC),
            'next_cron': datetime.datetime(2018, 10, 27, 1, 0).replace(tzinfo=pytz.UTC),
            'enforcements': [mock_enforcement]
        }

        result_value = sensor.check_enforcements(**test_dict)
        self.assertEqual(result_value, False)
        self.assertEqual(sensor.kv_enforcements, {'test_rule': 'test_id'})

    def test_check_enforcements_success_dispatch(self):
        sensor = self.get_sensor_instance()
        sensor.st2_fqdn = 'st2_test'
        sensor.kv_enforcements = {'test_rule': 'test_id'}

        mock_enforcement = mock.Mock(id='test_id',
                                     enforced_at='2018-10-26T01:00:00.01Z',
                                     execution_id='test_execution',
                                     rule={'ref': 'test_rule'})
        mock_execution = mock.Mock(status='success')

        mock_st2_client = mock.MagicMock()
        mock_st2_client.liveactions.get_by_id.return_value = mock_execution
        sensor.st2_client = mock_st2_client

        test_dict = {
            'previous_cron': datetime.datetime(2018, 10, 26, 1, 0).replace(tzinfo=pytz.UTC),
            'next_cron': datetime.datetime(2018, 10, 27, 1, 0).replace(tzinfo=pytz.UTC),
            'enforcements': [mock_enforcement]
        }

        trigger_payload = {
            'st2_rule_name': 'test_rule',
            'st2_server': 'st2_test',
            'st2_execution_id': 'test_execution',
            'st2_comments': 'Cronjob ran successfully',
            'st2_state': 'success'
        }

        result_value = sensor.check_enforcements(**test_dict)
        self.assertEqual(result_value, True)
        self.assertEqual(sensor.kv_enforcements, {'test_rule': 'test_id'})
        self.assertTriggerDispatched(trigger='errors.error_cron_event',
                                     payload=trigger_payload)

    def test_check_enforcements_no_execution(self):
        sensor = self.get_sensor_instance()
        sensor.st2_fqdn = 'st2_test'
        sensor.kv_enforcements = {}

        mock_enforcement = mock.Mock(spec=True,
                                     id="test_id",
                                     enforced_at='2018-10-26T01:00:00.01Z',
                                     rule={'ref': 'test_rule'})
        mock_rule_enforcement = mock.Mock(id="test_id",
                                         failure_reason="test_failure")

        mock_st2_client = mock.MagicMock()
        mock_st2_client.ruleenforcements.get_by_id.return_value = mock_rule_enforcement
        sensor.st2_client = mock_st2_client

        test_dict = {
            'previous_cron': datetime.datetime(2018, 10, 26, 1, 0).replace(tzinfo=pytz.UTC),
            'next_cron': datetime.datetime(2018, 10, 27, 1, 0).replace(tzinfo=pytz.UTC),
            'enforcements': [mock_enforcement]
        }

        trigger_payload = {
            'st2_rule_name': 'test_rule',
            'st2_server': 'st2_test',
            'st2_execution_id': '',
            'st2_comments': 'test_failure',
            'st2_state': 'error'
        }

        result_value = sensor.check_enforcements(**test_dict)
        self.assertEqual(result_value, False)
        self.assertTriggerDispatched(trigger='errors.error_cron_event',
                                     payload=trigger_payload)
        self.assertEqual(sensor.kv_enforcements, {'test_rule': 'test_id'})

    def test_check_enforcements_no_execution_jinja_escaping(self):
        sensor = self.get_sensor_instance()
        sensor.st2_fqdn = 'st2_test'
        sensor.kv_enforcements = {}

        mock_enforcement = mock.Mock(spec=True,
                                     id="test_id",
                                     enforced_at='2018-10-26T01:00:00.01Z',
                                     rule={'ref': 'test_rule'})
        mock_rule_enforcement = mock.Mock(id="test_id",
                                         failure_reason='{{ test_failure }}')

        mock_st2_client = mock.MagicMock()
        mock_st2_client.ruleenforcements.get_by_id.return_value = mock_rule_enforcement
        sensor.st2_client = mock_st2_client

        test_dict = {
            'previous_cron': datetime.datetime(2018, 10, 26, 1, 0).replace(tzinfo=pytz.UTC),
            'next_cron': datetime.datetime(2018, 10, 27, 1, 0).replace(tzinfo=pytz.UTC),
            'enforcements': [mock_enforcement]
        }

        # W605 = invalid escape sequence flake8 error that we want to ignore
        trigger_payload = {
            'st2_rule_name': 'test_rule',
            'st2_server': 'st2_test',
            'st2_execution_id': '',
            'st2_comments': '\{\{ test_failure \}\}',  # noqa: W605
            'st2_state': 'error'
        }

        result_value = sensor.check_enforcements(**test_dict)
        self.assertEqual(result_value, False)
        self.assertTriggerDispatched(trigger='errors.error_cron_event',
                                     payload=trigger_payload)
        self.assertEqual(sensor.kv_enforcements, {'test_rule': 'test_id'})

    def test_check_enforcements_true(self):
        sensor = self.get_sensor_instance()
        sensor.kv_enforcements = {}

        mock_enforcement = mock.Mock(enforced_at='2018-10-26T01:00:00.01Z',
                                    execution_id='test',
                                    rule={'ref': 'test_rule'})
        mock_execution = mock.Mock(status='succeeded')

        mock_st2_client = mock.MagicMock()
        mock_st2_client.liveactions.get_by_id.return_value = mock_execution
        sensor.st2_client = mock_st2_client

        test_dict = {
            'previous_cron': datetime.datetime(2018, 10, 26, 1, 0).replace(tzinfo=pytz.UTC),
            'next_cron': datetime.datetime(2018, 10, 27, 1, 0).replace(tzinfo=pytz.UTC),
            'enforcements': [mock_enforcement]
        }

        result_value = sensor.check_enforcements(**test_dict)
        self.assertEqual(result_value, True)

    def test_dispatch_trigger(self):
        sensor = self.get_sensor_instance()
        sensor.kv_enforcements = {}
        test_dict = {
            'st2_rule_name': 'test_rule',
            'st2_server': 'st2_test',
            'st2_execution_id': 'st2_test_execution',
            'st2_comments': 'test_comments',
            'st2_state': 'open'
        }

        sensor.dispatch_trigger(**test_dict)
        self.assertTriggerDispatched(trigger='errors.error_cron_event',
                                     payload=test_dict)

    def test_check_before_dispatch_no_keys(self):
        sensor = self.get_sensor_instance()
        sensor.kv_enforcements = {}
        test_dict = {
            'st2_rule_name': 'test_rule',
            'st2_enforcement_id': None
        }

        result_value = sensor.check_before_dispatch(**test_dict)
        self.assertEqual(result_value, True)

    def test_check_before_dispatch_no_keys_with_enforcement(self):
        sensor = self.get_sensor_instance()
        sensor.kv_enforcements = {}
        test_dict = {
            'st2_rule_name': 'test_rule',
            'st2_enforcement_id': 'test_enforcement'
        }

        result_value = sensor.check_before_dispatch(**test_dict)
        self.assertEqual(result_value, True)

    def test_check_before_dispatch_enforcement_id(self):
        sensor = self.get_sensor_instance()
        sensor.kv_enforcements = {'test_rule': 'test_enforcement'}
        test_dict = {
            'st2_rule_name': 'test_rule',
            'st2_enforcement_id': 'test_enforcement'
        }

        result_value = sensor.check_before_dispatch(**test_dict)
        self.assertEqual(result_value, False)

    def test_check_before_dispatch_no_enforcement_id(self):
        sensor = self.get_sensor_instance()
        sensor.kv_enforcements = {'test_rule': 'error without enforcement id'}
        test_dict = {
            'st2_rule_name': 'test_rule',
            'st2_enforcement_id': None
        }

        result_value = sensor.check_before_dispatch(**test_dict)
        self.assertEqual(result_value, False)

    def test_delete_from_kv(self):
        sensor = self.get_sensor_instance()
        sensor.kv_enforcements = {'test_rule': 'test_id', 'test_rule_2': 'test_id_2'}

        result_value = sensor.delete_from_kv('test_rule')
        self.assertEqual(result_value, {'test_rule_2': 'test_id_2'})

    def test_get_cron_rules(self):
        sensor = self.get_sensor_instance()
        first_name_property = mock.PropertyMock(return_value='test1')
        mock_rule1 = mock.Mock(trigger={'type': "core.st2.CronTimer"})
        type(mock_rule1).name = first_name_property

        second_name_property = mock.PropertyMock(return_value='test2')
        mock_rule2 = mock.Mock(trigger={'type': "core.st2.CronTimer"})
        type(mock_rule2).name = second_name_property

        third_name_property = mock.PropertyMock(return_value='test3')
        mock_rule3 = mock.Mock(trigger={'type': "not_cron"})
        type(mock_rule3).name = third_name_property

        mock_st2_client = mock.MagicMock()
        mock_st2_client.rules.query.return_value = [mock_rule1, mock_rule2, mock_rule3]
        sensor.st2_client = mock_st2_client

        result_value = sensor.get_cron_rules()
        self.assertEqual(result_value, [mock_rule1, mock_rule2])

    def test_convert_to_crontab_all(self):
        sensor = self.get_sensor_instance()
        test_dict = {
            'day_of_week': '*',
            'second': '*',
            'minute': '*',
            'hour': '*',
            'day': '*',
            'month': '*',
            'year': '*'
        }

        expected_return = '* * * * * * *'
        result_value = sensor.convert_to_crontab(test_dict)
        self.assertEqual(result_value, expected_return)

    def test_convert_to_crontab_missing(self):
        sensor = self.get_sensor_instance()
        test_dict = {
            'day_of_week': '*',
            'second': '*',
            'minute': '*',
            'day': '*',
            'year': '*'
        }

        expected_return = '* * * * * * *'
        result_value = sensor.convert_to_crontab(test_dict)
        self.assertEqual(result_value, expected_return)

    def test_convert_to_crontab_day_convert(self):
        sensor = self.get_sensor_instance()
        test_dict = {
            'day_of_week': 3,
            'second': '*',
            'minute': '*',
            'month': '*',
        }

        expected_return = '* * * * * 4 *'
        result_value = sensor.convert_to_crontab(test_dict)
        self.assertEqual(result_value, expected_return)
