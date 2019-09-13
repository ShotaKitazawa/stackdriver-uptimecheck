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
        config = monitoring_v3.types.uptime_pb2.UptimeCheckConfig()
        config.name = "projects/test/UptimeCheckConfigs/test"
        config.display_name = "test"
        config.monitored_resource.type = "uptime_url"
        config.monitored_resource.labels.update({"host": "example.net"})
        config.http_check.path = "/"
        config.http_check.port = 443
        config.http_check.use_ssl = True
        config.timeout.seconds = 10
        config.period.seconds = 300
        self.exist_config = config

    def list_uptime_check_configs(self, project_name):
        """
        project_name = "projects/XXX"
        """
        if project_name == "/".join(self.exist_config.name.split("/")[0:2]):
            return [self.exist_config]
        else:
            return []

    def get_uptime_check_config(self, api_path):
        """
        api_path = "projects/XXX/UptimeCheckConfigs/XXX"
        """
        if api_path == self.exist_config.name:
            return self.exist_config
        else:
            monitoring_v3.types.uptime_pb2.UptimeCheckConfig()

    def update_uptime_check_config(self, config, field_mask):
        """
        config = <class 'google.cloud.monitoring_v3.types.UptimeCheckConfig>
        field_mask = <class 'google.protobuf.field_mask_pb2.FieldMask'>
        """
        # TODO field_mask の内容をconfigに反映
        return config

    def create_uptime_check_config(self, project_name, config):
        """
        project_name = "projects/XXX"
        config = <class 'google.cloud.monitoring_v3.types.UptimeCheckConfig>
        """
        return (
            config
            if config.display_name not in self.list_uptime_check_configs(project_name)
            else None
        )


# converge_uptime_check テスト用のモック
def create_uptime_check_mock(project_name, config_name, target_uri, timeout_seconds, period_seconds):
    return "called create_uptime_check_config"


# converge_uptime_check テスト用のモック
def update_uptime_check_mock(project_name, config_name, target_uri, timeout_seconds, period_seconds):
    return "called update_uptime_check_config"


class Test:
    # parse_uri のテスト
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

    # UptimeCheckConfig クラスのテスト
    class TestUptimeCheck:
        uptime_check_config = converge_uptime_check.UptimeCheckConfig(test=True)
        uptime_check_config.client = GoogleClientMock()

        # createできることのテスト
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

        # updateできることのテスト
        def test_update_uptime_check_config(self):
            result = self.uptime_check_config.update_uptime_check_config(
                project_name="projects/test",
                config_name="test",
                target_uri="https://example.net",
                timeout_seconds=10,
                period_seconds=60,
            )
            # TODO: GoogleClientMock.update_uptime_check_config() の TODO 参照
            # assert result.display_name == "test"
            # assert result.monitored_resource.labels["host"] == "example.net"
            # assert result.http_check.path == "/"
            # assert result.http_check.port == 443
            # assert result.http_check.use_ssl
            # assert result.timeout.seconds == 10
            assert result.period.seconds == 60

        # ホストを変更してupdateするとraiseすることのテスト
        def test_update_uptime_check_config_fail(self):
            with pytest.raises(converge_uptime_check.MissingSpecifiedHost):
                self.uptime_check_config.update_uptime_check_config(
                    project_name="projects/test",
                    config_name="test",
                    target_uri="https://example.com",
                    timeout_seconds=10,
                    period_seconds=60,
                )

        # converge_uptime_check_config() の config_name なリソースが存在しないならば create_uptime_check_config() を呼び出すテスト
        def test_converge_uptime_check_config_01(self):
            self.uptime_check_config.create_uptime_check_config = create_uptime_check_mock
            self.uptime_check_config.update_uptime_check_config = update_uptime_check_mock
            assert self.uptime_check_config.converge_uptime_check_configs(
                project_name="projects/test",
                config_name="create_test",
                target_uri="https://example.net",
                timeout_seconds=10,
                period_seconds=300,
            ) == "called create_uptime_check_config"

        # converge_uptime_check_config() の config_name なリソースが既に存在するならば update_uptime_check_config() を呼び出すテスト
        def test_converge_uptime_check_config_02(self):
            self.uptime_check_config.create_uptime_check_config = create_uptime_check_mock
            self.uptime_check_config.update_uptime_check_config = update_uptime_check_mock
            assert self.uptime_check_config.converge_uptime_check_configs(
                project_name="projects/test",
                config_name="test",
                target_uri="https://example.net",
                timeout_seconds=10,
                period_seconds=300,
            ) == "called update_uptime_check_config"
