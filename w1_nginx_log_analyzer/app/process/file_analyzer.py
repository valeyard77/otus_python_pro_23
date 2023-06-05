import datetime
import gzip
import sys
import time
import re
import os
import logging

from dataclasses import dataclass
from datetime import datetime, MINYEAR
from typing import Union
from statistics import median


@dataclass(frozen=False)
class FileDescription:
    file_path: Union[str, None]
    date: datetime


class LogAnalyzer:
    def __init__(self, error_threshold: int = 40):
        self.url_dict = {}
        self.total_requests_time = 0.0
        self.total_requests_count = 0
        self.last_log = FileDescription(None, datetime(MINYEAR, 1, 1))
        self.error_threshold = error_threshold

    def find_last_log_file(self, nginx_logs_dir: str, nginx_file_mask: str = ".*"):
        logging.debug(f"Find last log file by mask {nginx_file_mask}")
        try:
            nginx_logs = [fn for fn in os.listdir(nginx_logs_dir) if
                          re.fullmatch(pattern=nginx_file_mask, string=fn, flags=re.IGNORECASE) is not None]
        except FileNotFoundError:
            logging.error(f"No such file or directory {nginx_logs_dir}")
            return None
        except Exception as e:
            exc = sys.exc_info()
            logging.error(e, exc_info=exc)
            return None

        for fn_log in nginx_logs:
            regex = re.search(pattern=r"log-(?P<dt>\d{8})", string=fn_log, flags=re.IGNORECASE)
            if regex is not None:
                file_dt = datetime.strptime(regex.group(1), "%Y%m%d")
                if file_dt > self.last_log.date:
                    self.last_log = FileDescription(f"{nginx_logs_dir}/{fn_log}", file_dt)

        return self

    def parse_log_file(self):
        """Parses log file and returns statistic data"""
        logging.debug('Parses log file and returns statistic data')
        for (request_url, request_time) in self.__parse_next_line():
            self.total_requests_time += request_time
            self.total_requests_count += 1
            if request_url not in self.url_dict:
                self.url_dict[request_url] = [request_time]
            else:
                self.url_dict[request_url].append(request_time)

        return self

    def __parse_next_line(self) -> Union[str, float]:
        start_time = time.perf_counter()
        parse_ok = 0
        parse_fail = 0
        regex_url = re.compile(
            pattern=r"(GET|POST|HEAD|PUT|DELETE|CONNECT|OPTIONS|TRACE|PATCH)\s(?P<req_uri>\/[^\s]*)\s+HTTP\/\d\.\d",
            flags=re.UNICODE + re.IGNORECASE
        )
        regex_time = re.compile(pattern=r"\"\s+(?P<timestamp>\d+\.\d{1,3})$", flags=re.IGNORECASE)
        with gzip.open(filename=self.last_log.file_path) if self.last_log.file_path.endswith('.gz') else open(self.last_log.file_path,
                                                                                          mode="rb") as stream:
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
        if failure_perc > self.error_threshold:
            raise SystemExit(f"File format error: {failure_perc}% lines wasn't parsed successfully")

    def analyze_log_file(self) -> list:
        stat_db = []
        for url, request_time_list in self.url_dict.items():
            val = {}
            val['count'] = len(request_time_list)
            val['time_sum'] = sum(request_time_list)
            val['time_max'] = max(request_time_list)
            val['time_avg'] = val['time_sum'] / val['count']
            val['url'] = url
            val['time_med'] = median(request_time_list)
            val['time_perc'] = val['time_sum'] * 100 / self.total_requests_time
            val['count_perc'] = len(request_time_list) * 100 / self.total_requests_count
            stat_db.append(val)
        return stat_db