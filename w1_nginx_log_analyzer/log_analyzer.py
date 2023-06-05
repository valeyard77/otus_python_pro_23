#!/usr/bin/env python
# -*- coding: utf-8 -*-
# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

import logging
import sys

from pathlib import Path
from app.library.config import AppConfig
from app.library.dependencies import CliParser
from app.process.file_analyzer import *
from app.process.file_analyzer import LogAnalyzer
from app.process.create_report import LogReport


def logger_init(log_level: int = logging.INFO, log_directory: str = None):
    filename = None
    if log_directory is not None:
        Path(log_directory).mkdir(exist_ok=True, parents=True)
        filename = Path(log_directory).joinpath(f"{Path(__file__).name[:-3]}.log").__str__()

    logging.basicConfig(level=log_level,
                        format='[%(asctime)s] %(levelname).1s %(message)s',
                        datefmt='%Y.%m.%d %H:%M:%S', filename=filename, filemode='a+'
                        )


def main():
    # initialize the ArgumentParser and read the parameters from the command line, if any
    args = CliParser()

    # reading the configuration file. If the file was not transferred, the default settings will be applied.
    cfg = AppConfig().load_config_file(config_file=args.config)
    if isinstance(cfg, Exception):
        logging.error(cfg)
        sys.exit()

    logger_init(log_level=logging.INFO if not args.debug else logging.DEBUG, log_directory=cfg.LOGS)
    logging.info("Nginx parser application started")

    logging.info("Find last log file by date and analyze it")
    lfa = LogAnalyzer(error_threshold=cfg.ERROR_THRESHOLD). \
        find_last_log_file(nginx_logs_dir=cfg.LOG_DIR, nginx_file_mask=cfg.NGINX_FILE_MASK)

    if lfa is None:
        sys.exit()

    logging.info(f"Analysing file {lfa.last_log.file_path}")
    statistic_db = lfa.parse_log_file().analyze_log_file()

    # create report
    report_filename = os.path.join(cfg.REPORT_DIR, f"report-{lfa.last_log.date.strftime('%Y.%m.%d')}.html")
    if LogReport(data=statistic_db,
                 report_template=Path(cfg.TEMPLATE_DIR).joinpath('report.html').__str__(),
                 report_filename=report_filename,
                 report_size=cfg.REPORT_SIZE).generate_report():
        logging.info(f"Report was generated to {report_filename}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info('process terminated')
