# Copyright 2018 Google LLC
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

# Ref: https://github.com/GoogleCloudPlatform/python-docs-samples/blob/master/monitoring/api/v3/uptime-check-client/snippets.py

from __future__ import print_function

import pytest
from google.cloud import monitoring_v3

import converge_uptime_check


class GoogleClientMock:
    """
    monitoring_v3.UptimeCheckServiceClient() のモッククラス
    既にStackdriver上に以下のUptime Checkの設定がある想定
    --------
    name: "projects/test/uptimeCheckConfigs/test"
    display_name: "test"
    monitored_resource {
      type: "uptime_url"
      labels {
        key: "host"
        value: "example.net"
      }
      labels {
        key: "project_id"
        value: "test"
      }
    }
    http_check {
      use_ssl: true
      path: "/"
      port: 443
    }
    period {
      seconds: 300
    }
    timeout {
      seconds: 10
    }
    """

    def __init__(self):
        pass

    def list_uptime_check_configs(self, project_name):
        if project_name == "projects/test":
            config = monitoring_v3.types.uptime_pb2.UptimeCheckConfig()
            config.name = "project/test/UptimeCheckConfigs/test"
            config.display_name = "test"
            config.monitored_resource.type = "uptime_url"
            config.monitored_resource.labels.update({"host": "example.net"})
            config.http_check.path = "/"
            config.http_check.port = 443
            config.http_check.use_ssl = True
            config.timeout.seconds = 10
            config.period.seconds = 300
            return [config]
        else:
            return []

    def get_uptime_check_config(self, config_name):
        result = self.list_uptime_check_configs("projects/test")[0]
        return (
            result
            if not result == "" and result.display_name == config_name
            else monitoring_v3.types.uptime_pb2.UptimeCheckConfig()
        )

    def update_uptime_check_config(self, project_name, field_mask):
        # TODO
        # return (
        #     config
        #     if config.display_name == self.list_uptime_check_configs(project_name)[0]
        #     else None
        # )

    def create_uptime_check_config(self, project_name, config):
        return (
            config
            if config.display_name != self.list_uptime_check_configs(project_name)[0]
            else None
        )


class Test:
    class TestParseURI:
        def test_parse_uri_success_01(self):
            uri = "http://example.com/path/to/"
            proto, host, port, path = converge_uptime_check.parse_uri(uri)
            assert proto == "http"
            assert host == "example.com"
            assert port == 80
            assert path == "/path/to/"

        def test_parse_uri_success_02(self):
            uri = "https://example.com"
            proto, host, port, path = converge_uptime_check.parse_uri(uri)
            assert proto == "https"
            assert host == "example.com"
            assert port == 443
            assert path == "/"

        def test_parse_uri_fail__missing_specified_port(self):
            uri = "http://example.com:hoge/path/to/"
            with pytest.raises(converge_uptime_check.MissingSpecifiedPort):
                proto, host, port, path = converge_uptime_check.parse_uri(uri)
            uri = "ws://example.com/"
            with pytest.raises(converge_uptime_check.MissingSpecifiedPort):
                proto, host, port, path = converge_uptime_check.parse_uri(uri)

        def test_parse_uri_fail__invalid_url(self):
            uri = "hogefugapiyo"
            with pytest.raises(converge_uptime_check.InvalidURL):
                proto, host, port, path = converge_uptime_check.parse_uri(uri)
            uri = "http://example.com:80:80/"
            with pytest.raises(converge_uptime_check.InvalidURL):
                proto, host, port, path = converge_uptime_check.parse_uri(uri)

    class TestUptimeCheck:
        uptime_check_config = converge_uptime_check.UptimeCheckConfig(test=True)
        uptime_check_config.client = GoogleClientMock()

        def test_create_uptime_check_config(self):
            result = self.uptime_check_config.create_uptime_check_config(
                project_name="projects/test",
                config_name="create_test",
                target_uri="http://example.com",
                timeout_seconds=10,
                period_seconds=300,
            )
            assert result.display_name == "create_test"
            assert result.monitored_resource.labels["host"] == "example.com"
            assert result.http_check.path == "/"
            assert result.http_check.port == 80
            assert not result.http_check.use_ssl
            assert result.timeout.seconds == 10
            assert result.period.seconds == 300

        def test_update_uptime_check_config(self):
            result = self.uptime_check_config.update_uptime_check_config(
                project_name="projects/test",
                config_name="test",
                target_uri="https://example.net",
                timeout_seconds=10,
                period_seconds=60,
            )
            assert result.display_name == "test"
            assert result.monitored_resource.labels["host"] == "example.net"
            assert result.http_check.path == "/"
            assert result.http_check.port == 443
            assert result.http_check.use_ssl
            assert result.timeout.seconds == 10
            assert result.period.seconds == 60

        # def test_update_uptime_check_config_fail(self):
        #     with pytest.raises(converge_uptime_check.MissingSpecifiedHost):
        #         self.uptime_check_config.update_uptime_check_config(
        #             project_name="projects/test",
        #             config_name="test",
        #             target_uri="https://example.com",
        #             timeout_seconds=10,
        #             period_seconds=60,
        #         )
