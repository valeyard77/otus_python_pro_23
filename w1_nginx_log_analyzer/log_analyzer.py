#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ex: https://github.com/Ampermetr123/otus-python/blob/103600f385ade8e4f7061380ddadb990d8f09fef/01_advanced_basics/log_analyzer/log_analyzer.py#L113

# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

import datetime
#import fnmatch
import gzip
import json
import os
import re
import logging
import time

from string import Template
from statistics import median
from dataclasses import dataclass
from datetime import datetime, MINYEAR
from typing import Union


@dataclass(frozen=True)
class Config:
    report_size: int = 1000
    report_dir: str = "./reports"
    template_dir: str = "asserts/templates"
    logs_dir: str = "./data"
    error_threshold: int = 40
    nginx_file_mask: str = r"nginx-access-ui\.log-(?P<date>\d{8})(\.gz)?$"


@dataclass(frozen=False)
class FileDescription:
    file_path: Union[str, None]
    date: datetime


def log_init(log_level: int, log_filename: str = None):
    logging.basicConfig(level=log_level, format='[%(asctime)s] %(levelname).1s %(message)s',
                        datefmt='%Y.%m.%d %H:%M:%S', filename=log_filename, filemode='a+')


def find_last_log_file(cfg: Config) -> FileDescription:
    last_log = FileDescription(None, datetime(MINYEAR, 1, 1))
    nginx_logs = [fn for fn in os.listdir(cfg.logs_dir) if
                  re.fullmatch(pattern=cfg.nginx_file_mask, string=fn, flags=re.IGNORECASE) is not None]
    for fn_log in nginx_logs:
        regex = re.search(pattern=r"log-(?P<dt>\d{8})", string=fn_log, flags=re.IGNORECASE)
        if regex is not None:
            file_dt = datetime.strptime(regex.group(1), "%Y%m%d")
            if file_dt > last_log.date:
                last_log = FileDescription(f"{cfg.logs_dir}/{fn_log}", file_dt)

    return last_log


def parse_next_line(log_name: str, error_threshold: int) -> (str, float):
    start_time = time.perf_counter()
    parse_ok = 0
    parse_fail = 0
    regex_url = re.compile(
        pattern=r"(GET|POST|HEAD|PUT|DELETE|CONNECT|OPTIONS|TRACE|PATCH)\s(?P<req_uri>\/[^\s]*)\s+HTTP\/\d\.\d",
        flags=re.UNICODE + re.IGNORECASE
    )
    regex_time = re.compile(pattern=r"\"\s+(?P<timestamp>\d+\.\d{1,3})$", flags=re.IGNORECASE)
    with gzip.open(filename=log_name) if log_name.endswith('.gz') else open(log_name, mode="rb") as stream:
        for s in stream:
            line = s.decode(encoding='UTF-8')
            match_url = regex_url.search(line)
            if match_url is None:
                parse_fail += 1
                continue
            req_url = match_url.group('req_uri')
            match_time = regex_time.search(line)
            if match_time is None:
                parse_fail += 1
                continue
            parse_ok += 1
            response_time = float(match_time.group('timestamp'))
            yield req_url, response_time

    logging.debug(
        f'{parse_ok} lines parsed from {parse_ok + parse_fail}, parse time is {round(time.perf_counter() - start_time, 2)} sec')

    failure_perc = 100 if parse_ok == 0 else parse_fail * 100 // (parse_ok + parse_fail)
    if failure_perc > error_threshold:
        logging.error(f"File format error: {failure_perc}% lines wasn't parsed successfully")


def analyse_log_file(log_name: str, error_threshold: int = 40) -> list:
    """Parses log file and returns statistic data"""
    url_dict = {}
    total_requests_time = 0.0
    total_requests_count = 0
    for (request_url, request_time) in parse_next_line(log_name=log_name, error_threshold=error_threshold):
        total_requests_time += request_time
        total_requests_count += 1
        if request_url not in url_dict:
            url_dict[request_url] = [request_time]
        else:
            url_dict[request_url].append(request_time)

    stat_db = []
    for url, request_time_list in url_dict.items():
        val = dict()
        val['count'] = len(request_time_list)
        val['time_sum'] = sum(request_time_list)
        val['time_max'] = max(request_time_list)
        val['time_avg'] = val['time_sum'] / val['count']
        val['url'] = url
        val['time_med'] = median(request_time_list)
        val['time_perc'] = val['time_sum'] * 100 / total_requests_time
        val['count_perc'] = len(request_time_list) * 100 / total_requests_count
        stat_db.append(val)
    return stat_db


def generate_report(data: list, report_template: str, report_filename: str, report_size: int = None) -> bool:
    """Writes report of statistic data to file."""
    if report_size is None:
        report_size = len(data)
    if report_size < len(data):
        selected = sorted(data, key=lambda x: x['time_sum'], reverse=True)
        data = selected[:report_size]

    # converts floats to string for better view in report
    for d in data:
        d['time_med'] = "%.3f" % (d['time_med'])
        d['time_perc'] = "%.3f" % (d['time_perc'])
        d['time_avg'] = "%.3f" % (d['time_avg'])
        d['count_perc'] = "%.3f" % (d['count_perc'])
        d['time_sum'] = "%.3f" % (d['time_sum'])

    json_data = json.dumps(data)

    with open(report_template, mode='r', encoding='utf-8') as tf:
        template = Template(tf.read())

    with open(report_filename, mode='w', encoding='utf-8') as rf:
        rf.write(template.safe_substitute(table_json=json_data))

    return True


def main():
    c = Config()
    log_init(log_level=logging.DEBUG)
    logging.info("Nginx parser application started")
    logging.info("Find last log file by date")
    last_log_fn = find_last_log_file(cfg=c)
    logging.debug(f"Last log file {last_log_fn.file_path}")

    # checking if report file already exists for this date
    report_filename = os.path.join(c.report_dir, f"report-{last_log_fn.date.strftime('%Y.%m.%d')}.html")
    if os.path.exists(report_filename):
        logging.info(f"File {report_filename} already exists")
        exit(0)

    # analyzing file
    logging.info(f'Analysing file {last_log_fn.file_path}')
    statistic_db = analyse_log_file(log_name=last_log_fn.file_path, error_threshold=c.error_threshold)

    # create report
    generate_report(data=statistic_db,
                    report_template=os.path.join(c.template_dir, 'report.html'),
                    report_filename=report_filename,
                    report_size=c.report_size)
    logging.info(f"Report was generated to {report_filename}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('process terminated')
