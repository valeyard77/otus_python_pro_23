#!/usr/bin/env python
# -*- coding: utf-8 -*-
# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

import logging

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
    # инициализируем ArgumentParser и считываем параметры из командной строки при их наличии
    args = CliParser()

    # Считываем конфигурационный файл. В случае если файл передан не был, будут применены параметры по умолчанию
    cfg = AppConfig().load_config_file(config_file=args.config)
    if isinstance(cfg, Exception):
        logging.error(cfg)
        exit(255)

    logger_init(log_level=logging.INFO if not args.debug else logging.DEBUG, log_directory=cfg.log_dir)
    logging.info("Nginx parser application started")

    # logging.info("Find last log file by date")
    # last_log_fn = find_last_log_file(cfg=cfg)
    # logging.debug(f"Last log file {last_log_fn.file_path}")
    #
    # # checking if report file already exists for this date
    # report_filename = os.path.join(cfg.report_dir, f"report-{last_log_fn.date.strftime('%Y.%m.%d')}.html")
    # if os.path.exists(report_filename):
    #     logging.info(f"File {report_filename} already exists")
    #     exit(0)
    #
    # # analyzing file
    # logging.info(f'Analysing file {last_log_fn.file_path}')
    # statistic_db = analyse_log_file(log_name=last_log_fn.file_path, error_threshold=c.error_threshold)

    logging.info("Find last log file by date and analyze it")
    lfa = LogAnalyzer(error_threshold=cfg.error_threshold). \
        find_last_log_file(nginx_logs_dir=cfg.nginx_logs_dir, nginx_file_mask=cfg.nginx_file_mask)

    logging.info(f'Analysing file {lfa.last_log.file_path}')
    statistic_db = lfa.analyse_log_file()

    # create report
    report_filename = os.path.join(cfg.report_dir, f"report-{lfa.last_log.date.strftime('%Y.%m.%d')}.html")
    if LogReport(data=statistic_db,
                 report_template=Path(cfg.template_dir).joinpath('report.html').__str__(),
                 report_filename=report_filename,
                 report_size=cfg.report_size).generate_report():
        logging.info(f"Report was generated to {report_filename}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info('process terminated')
