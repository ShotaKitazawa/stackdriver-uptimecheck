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

import argparse
import os
import urllib.parse

from google.cloud import monitoring_v3


class MissingProjectIdError(Exception):
    pass


class InvalidURL(Exception):
    pass


class MissingUptimeCheckProto(Exception):
    pass


class MissingSpecifiedHost(Exception):
    pass


class MissingSpecifiedPort(Exception):
    pass


def parse_uri(uri):
    o = urllib.parse.urlparse(uri)
    if o.scheme == "":
        raise InvalidURL("Invalid URL")

    host = o.netloc.split(":")[0]
    if len(o.netloc.split(":")) == 1:
        if o.scheme == "http":
            port = 80
        elif o.scheme == "https":
            port = 443
        else:
            raise MissingSpecifiedPort("Port must specify")
    elif len(o.netloc.split(":")) == 2:
        if not o.netloc.split(":")[1].isdecimal():
            raise MissingSpecifiedPort("Port is not integer")
        port = int(o.netloc.split(":")[1])
    else:
        raise InvalidURL("Invalid URL")

    return o.scheme, host, port, o.path if not o.path == "" else "/"


def project_id():
    project_id = os.environ["GCLOUD_PROJECT"]

    if not project_id:
        raise MissingProjectIdError(
            "Set the environment variable "
            + "GCLOUD_PROJECT to your Google Cloud Project Id."
        )
    return project_id


def project_name(project=None):
    if project:
        return "projects/" + project
    else:
        return "projects/" + project_id()


class UptimeCheckConfig:
    def __init__(self, test=False):
        if not test:
            self.client = monitoring_v3.UptimeCheckServiceClient()
        else:
            self.client = None

    def get_uptime_check_config(self, project_name, config_name):
        configs = self.client.list_uptime_check_configs(project_name)
        for config in configs:
            if config.display_name == config_name:
                return config
        else:
            return None

    def update_uptime_check_config(
        self, project_name, config_name, target_uri, timeout_seconds, period_seconds
    ):
        proto, host, port, path = parse_uri(target_uri)
        previous_config = self.get_uptime_check_config(project_name, config_name)
        api_path = previous_config.name

        if host != previous_config.monitored_resource.labels["host"]:
            raise MissingSpecifiedHost(
                "Hostname on current and previous config are defferent. Must to be the same."
            )

        config = self.client.get_uptime_check_config(api_path)
        field_mask = monitoring_v3.types.FieldMask()

        if path != previous_config.http_check.path:
            field_mask.paths.append("http_check.path")
            config.http_check.path = path
        if proto == "http" or proto == "https":
            if path != previous_config.http_check.path:
                field_mask.paths.append("http_check.path")
                config.http_check.path = path
            if port != previous_config.http_check.port:
                field_mask.paths.append("http_check.port")
                config.http_check.port = port
            if (previous_config.http_check.use_ssl and proto == "http") or (
                not previous_config.http_check.use_ssl and proto == "https"
            ):
                field_mask.paths.append("http_check.use_ssl")
                config.http_check.port = config.http_check.use_ssl = (
                    True if proto == "https" else False
                )
        elif proto == "tcp":
            if port != previous_config.tcp_check.port:
                field_mask.paths.append("tcp_check.port")
                config.tcp_check.port = port
        else:
            raise MissingUptimeCheckProto("Unsuport ProtoType")
        if timeout_seconds != previous_config.timeout.seconds:
            field_mask.paths.append("timeout.seconds")
            config.timeout.seconds = timeout_seconds
        if period_seconds != previous_config.period.seconds:
            field_mask.paths.append("period.seconds")
            config.period.seconds = period_seconds

        return self.client.update_uptime_check_config(config, field_mask)

    def create_uptime_check_config(
        self, project_name, config_name, target_uri, timeout_seconds, period_seconds
    ):
        proto, host, port, path = parse_uri(target_uri)
        config = monitoring_v3.types.uptime_pb2.UptimeCheckConfig()
        config.display_name = config_name
        config.monitored_resource.type = "uptime_url"
        config.monitored_resource.labels.update({"host": host})
        if proto == "http" or proto == "https":
            config.http_check.path = path
            config.http_check.port = port
            config.http_check.use_ssl = True if proto == "https" else False
        elif proto == "tcp":
            config.tcp_check.port = port
        else:
            raise MissingUptimeCheckProto("Unsuport ProtoType")
        config.timeout.seconds = timeout_seconds
        config.period.seconds = period_seconds

        return self.client.create_uptime_check_config(project_name, config)

    def converge_uptime_check_configs(
        self, project_name, config_name, target_uri, timeout_seconds, period_seconds
    ):
        timeout_seconds_int = timeout_seconds if timeout_seconds else 10
        period_seconds_int = period_seconds if period_seconds else 300
        if self.get_uptime_check_config(project_name, config_name):
            return self.update_uptime_check_config(
                project_name,
                config_name,
                target_uri,
                timeout_seconds_int,
                period_seconds_int,
            )
        else:
            return self.create_uptime_check_config(
                project_name,
                config_name,
                target_uri,
                timeout_seconds_int,
                period_seconds_int,
            )


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Uptime Check API operations.")
    parser.add_argument("-n", "--uptime_check_name", required=True)
    parser.add_argument("-t", "--uptime_check_target", required=True)
    parser.add_argument("--timeout_seconds", required=False)
    parser.add_argument("--period_seconds", required=False)
    parser.add_argument("--project", required=False)
    args = parser.parse_args()

    uptime_check_config = UptimeCheckConfig()

    print("----------")
    print(
        uptime_check_config.converge_uptime_check_configs(
            project_name(args.project),
            args.uptime_check_name,
            args.uptime_check_target,
            args.timeout_seconds,
            args.period_seconds,
        )
    )
