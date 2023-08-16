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

import pandas as pd
import glob
import datetime
import sys

import threading
import subprocess as sub
import os
import re
import time
from idle_checker import log_a_point


"""
Call this from a daemon process that run this every X minutes. Decides whether or not to
shutdown an inactive VM running a Jupyter Notebook Server on a Google VM. Steps:

1) Check the last X hours of activity logs to see if the machine has been active. Have
accumlated empirical stats on what consistitutes an idle VM, where there is e.g. basal
network activity no matter what. Note those thresholds will be exceeded at least once a
day by Google VM maintenance logging, etc. That is not accounted for.

2) Previous logs might be ~10 minutes old. If we pass the first test, do a final check
of new Stackdriver metrics to see if there is recent activity.

3) User might still be starting to use the machine again in the last minute or two. If we
pass the first two checks, run two processes for X seconds in parallel to check TCP traffic
off the server port, and to check CPU usage of all (first generation only!) child processes
of the Notebook server.

4) If all previous checks indicate a shutdown is warranted, return True, else return False.

"""

def do_a_type(full_frame, tag, subtag, val_type, start_stamp, end_stamp, thresh):
    """
    Decide if the specified type can be considered active during the given time period
    """
    df_sb = full_frame.loc[full_frame['Type'] == tag]
    df_sb.Time.str.replace(r'(\d+)-(\d+)-(\d+)-(.+)', r'\1-\2-\3 \4')
    df_sb = df_sb.astype({"Time": 'datetime64', "Value": val_type})
    df_sb.rename(columns={"Value": subtag}, inplace=True)
    df_sb.set_index("Time", inplace=True)
    dfsl = df_sb.loc[start_stamp:end_stamp]
    not_idle = dfsl[subtag].max() > thresh
    return not_idle

def pull_from_logs(home_dir, log_dir):
    """
    Pull in all the logs into a pandas data frame. Note the way the logging is done, multiple copies
    of the same time stamp can appear in the log
    """

    full_glob = "{}/{}/{}".format(home_dir, log_dir, '@4*.s')
    current_file = "{}/{}/{}".format(home_dir, log_dir, 'current')

    fgs = glob.glob(full_glob)
    fgs.append(current_file)
    uniq_lines = {}
    for use_file_name in fgs:
        with open(use_file_name, 'r') as readfile:
            for line in readfile:
                split_line = line.rstrip('\n').split()
                sub_line = ' '.join(split_line[2:5])
                uniq_lines[sub_line] = tuple(split_line[2:5])

    tuple_list = []
    for key in sorted(uniq_lines):
        tuple_list.append(uniq_lines[key])

    all_types = pd.DataFrame.from_records(tuple_list, columns=["Type", "Time", "Value"])
    return all_types

def pull_from_list(series_list):
    """
    Pull in all list entries into a pandas data frame. Note the way the logging is done, multiple copies
    of the same time stamp can appear in the log. Note also that coming from a list, we do NOT have a log
    time stamp to worry about in position 1
    """

    uniq_lines = {}
    for line in series_list:
        split_line = line.rstrip('\n').split()[1:4]
        uniq_lines[line] = tuple(split_line)

    tuple_list = []
    for key in sorted(uniq_lines):
        tuple_list.append(uniq_lines[key])

    all_types = pd.DataFrame.from_records(tuple_list, columns=["Type", "Time", "Value"])
    return all_types

def are_we_busy(all_types, window_hours, idle_thresh):
    """
    Decide if machine is busy based upon several measurements
    """
    now = time.time()
    start_stamp = now - (60 * 60 * window_hours)
    now_st = datetime.datetime.fromtimestamp(now).strftime('%Y-%m-%d %H:%M:%S')
    start_st = datetime.datetime.fromtimestamp(start_stamp).strftime('%Y-%m-%d %H:%M:%S')
    print("now {} type {} stamp {}".format(now, type(now), now_st))

    not_idle_sb = do_a_type(all_types, 'network/sent_bytes_count', 'sent_bytes_count', 'int',
                            start_st, now_st, idle_thresh['sent_bytes_count'])
    not_idle_cb = do_a_type(all_types, 'network/received_bytes_count', 'received_bytes_count', 'int',
                            start_st, now_st, idle_thresh['received_bytes_count'])
    not_idle_wb = do_a_type(all_types, 'disk/write_bytes_count', 'write_bytes_count', 'int',
                            start_st, now_st, idle_thresh['write_bytes_count'])
    not_idle_wo = do_a_type(all_types, 'disk/write_ops_count', 'write_ops_count', 'int',
                            start_st, now_st, idle_thresh['write_ops_count'])
    not_idle_rb = do_a_type(all_types, 'disk/read_bytes_count', 'read_bytes_count', 'int',
                            start_st, now_st, idle_thresh['read_bytes_count'])
    not_idle_ro = do_a_type(all_types, 'disk/read_ops_count', 'read_ops_count', 'int',
                            start_st, now_st, idle_thresh['read_ops_count'])
    not_idle_ut = do_a_type(all_types, 'cpu/utilization', 'utilization', 'float64',
                            start_st, now_st, idle_thresh['utilization'])

    keep_alive = not_idle_sb or not_idle_cb or not_idle_wb or not_idle_wo or not_idle_rb or not_idle_ro or not_idle_ut

    return keep_alive


def tcp_says_idle(check_secs, port_num, thresh, answer):
    """
    Check traffic on the jupyter notebook server port. Note there are heartbeat packets even if nobody
    is at the keyboard; thresh should take this into account (empirical: > 100 means something is happening
    """
    am_idle = True
    #
    # We only get away with this as a regular user is because everybody can sudo on a Google VM:
    #
    p = sub.Popen(('sudo', 'timeout', str(check_secs), 'tcpdump', '-l', 'port', port_num), stdout=sub.PIPE, stderr=sub.DEVNULL)
    for line in iter(p.stdout.readline, b''):
        pack_val_str = re.sub('.*length', '', line.rstrip().decode("utf-8")).strip()
        if pack_val_str and (int(pack_val_str) > thresh):
            am_idle = False
    p.wait()  # to get rid of defunct process. Since we know it is done, it will not pause
    answer[0] = am_idle
    return


def top_says_idle(check_secs, thresh, home_dir, answer):
    """
    Check cpu usage for all processes that are children of the process listening on the jupyter notebook
    server port. Uses top, so tiny cpu % may not appear.
    """

    am_idle = True
    for i in range(0, check_secs):
        p = sub.Popen(('{}/cpulogger2.sh'.format(home_dir)), stdout=sub.PIPE)
        for line in iter(p.stdout.readline, b''):
            cpu_val_str = line.rstrip().decode("utf-8").split()[8]
            try:
                cpu_val = float(cpu_val_str)
            except ValueError:
                print("cpu not a float %s\n" % cpu_val_str)
                continue
            if cpu_val > thresh:
                am_idle = False
        p.wait()  # to get rid of defunct process
        if not am_idle:
            answer[0] = am_idle
            return
        time.sleep(1)
    answer[0] = am_idle
    return

def shutdown_decision(home_dir, log_dir, window_hours, gcp_project_id, instance_name, port_num):
    #
    # Based on empirical observations of lull times, values above these indicate the
    # machine is not idle. Note that running *this job* seems to bump the utilization up to
    # 0.027 - 0.033 every fourth and fifth minute. Otherwise it appears to be less than 0.01.
    # If this turns out to be a problem, we could filter those points out. Or we could take the
    # average usage and see if it is exceeded.
    #

    idle_thresh = {
        'sent_bytes_count': 15000,
        'received_bytes_count': 90000,
        'write_bytes_count': 250000,
        'write_ops_count': 30,
        'read_bytes_count': 10,
        'read_ops_count': 10,
        'utilization': 0.036
    }
    interval_sec = 600
    final_secs = 60
    tcp_thresh = 100
    final_cpu = 0.0

    #
    # First decision is to see if we consider ourselves idle over the last X hours. If we are active, we are done
    #
    all_types = pull_from_logs(home_dir, log_dir)
    if are_we_busy(all_types, window_hours, idle_thresh):
        print("last hour busy")
        return False
    #
    # If we are idle in the long term, check to see if we have been idle recently. The long-term logging
    # may not have run for the last several minutes:
    #

    series_list = log_a_point(gcp_project_id, instance_name, interval_sec, False)
    all_types = pull_from_list(series_list)
    if are_we_busy(all_types, window_hours, idle_thresh):
        print("recently busy")
        return False

    #
    # If the latest data says we are idle, then we monitor port usage for the server, and top data for
    # CPU usage for every child process of the server to see if we are idle. Even mre extreme, we
    # *could* attach strace to the processes to see if they are doing anything at all. For now, let's
    # not do that

    tcp_answer = [False]
    cpu_answer = [False]
    t1 = threading.Thread(target = tcp_says_idle, args=(final_secs, port_num, tcp_thresh, tcp_answer))
    t2 = threading.Thread(target=top_says_idle, args=(final_secs, final_cpu, home_dir, cpu_answer))

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    print("recent tcp %s\n" % tcp_answer[0])
    print("recent cpu %s\n" % cpu_answer[0])

    return tcp_answer[0] or cpu_answer[0]


def main(args):
    home_dir = args[1]
    log_dir = args[2]
    window_hours = int(args[3])
    gcp_project_id = args[4]
    instance_name = args[5]
    port_num = args[6]

    do_shutdown = shutdown_decision(home_dir, log_dir, window_hours, gcp_project_id, instance_name, port_num)
    return do_shutdown

if __name__ == "__main__":
    main(sys.argv)