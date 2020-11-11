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
import yaml
import json
import codecs
import logging

from st2tests.base import BaseActionTestCase


class ErrorsBaseActionTestCase(BaseActionTestCase):
    __test__ = False

    def setUp(self):
        super(ErrorsBaseActionTestCase, self).setUp()
        logging.disable(logging.CRITICAL) # disable logging

    def tearDown(self):
        super(ErrorsBaseActionTestCase, self).tearDown()
        logging.disable(logging.CRITICAL) # disable logging

    def load_yaml(self, filename):
        return yaml.safe_load(self.get_fixture_content(filename))

    def load_json(self, filename):
        return json.loads(self.get_fixture_content(filename))

    def load_html_file(self, filename):
        html_file = codecs.open(os.path.join(os.path.dirname(__file__), 'fixtures', filename), 'r')
        return html_file.read()
