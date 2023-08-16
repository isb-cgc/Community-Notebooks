"""
Copyright 2019, Institute for Systems Biology

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

"""
Used as a daemon process to generate logs of system activity using the Stackdriver monitoring
system on Google VMs. Note that project and VM must have Stackdriver monitoring enabled. Note
that this just writes out lines to stdout, and should be wrapped by idle_log_wrapper.sh to
route the output to a set of rolled logs with a maximum size limit that covers enough history
to decide if we are idle.

Function log_a_point() can also be called in single-shot mode to provide a list of entries for
recent activity (multilog appears to do buffering, some Stackdriver metrics take 240 seconds to
refresh, and history logs might be several minutes old).
"""

from google.cloud import monitoring_v3
import sys
from datetime import datetime
import time

def get_a_series(client, project_name, interval, instance, metric, print_it):
    results = client.list_time_series(
        project_name,
        'metric.type = "compute.googleapis.com/instance/{}" AND '
        'metric.label.instance_name = "{}"'.format(metric, instance),
        interval,
        monitoring_v3.enums.ListTimeSeriesRequest.TimeSeriesView.FULL)

    series_lines = []
    for result in results:
        type_name = result.metric.type.replace("compute.googleapis.com/instance/", "")
        instance_name = result.metric.labels['instance_name']
        is_float = result.value_type == monitoring_v3.enums.MetricDescriptor.ValueType.DOUBLE
        for point in result.points:
            date_string = datetime.utcfromtimestamp(float(point.interval.end_time.seconds)).strftime('%Y-%m-%d-%H:%M:%S')
            value = point.value.double_value if is_float else point.value.int64_value
            out_line = "{} {} {} {}".format(instance_name, type_name, date_string, value)
            series_lines.append(out_line)
            if print_it:
                print(out_line)

    return series_lines

def log_a_point(gcp_project_id, instance_name, interval_sec, print_it):
    client = monitoring_v3.MetricServiceClient()
    project_name = client.project_path(gcp_project_id)

    interval = monitoring_v3.types.TimeInterval()
    now = time.time()
    interval.end_time.seconds = int(now)
    interval.end_time.nanos = int(
        (now - interval.end_time.seconds) * 10 ** 9)
    interval.start_time.seconds = int(now - interval_sec)
    interval.start_time.nanos = interval.end_time.nanos

    #
    # Some of these numbers are only visible again 240 seconds after last query! Poll
    # at an appropriate interval!
    #

    all_series = []
    all_series += get_a_series(client, project_name, interval, instance_name, "cpu/utilization", print_it)
    all_series += get_a_series(client, project_name, interval, instance_name, "cpu/reserved_cores", print_it)
    all_series += get_a_series(client, project_name, interval, instance_name, "cpu/usage_time", print_it)
    all_series += get_a_series(client, project_name, interval, instance_name, "disk/read_bytes_count", print_it)
    all_series += get_a_series(client, project_name, interval, instance_name, "disk/write_bytes_count", print_it)
    all_series += get_a_series(client, project_name, interval, instance_name, "disk/read_ops_count", print_it)
    all_series += get_a_series(client, project_name, interval, instance_name, "disk/write_ops_count", print_it)
    all_series += get_a_series(client, project_name, interval, instance_name, "network/sent_bytes_count", print_it)
    all_series += get_a_series(client, project_name, interval, instance_name, "network/received_bytes_count", print_it)
    return all_series

def main(args):
    gcp_project_id = args[1]
    instance_name = args[2]
    interval_sec = int(args[3])
    sleep_secs = int(args[4])
    while True:
        log_a_point(gcp_project_id, instance_name, interval_sec, True)
        time.sleep(sleep_secs)

if __name__ == "__main__":
    main(sys.argv)