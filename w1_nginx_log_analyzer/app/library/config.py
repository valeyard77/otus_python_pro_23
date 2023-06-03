import sys
import json

from dataclasses import dataclass
from typing import Union


@dataclass(frozen=False)
class AppConfig:
    log_dir: str = None
    report_size: int = 1000
    report_dir: str = "./reports"
    template_dir: str = "app/resources/templates"
    nginx_logs_dir: str = "./data"
    error_threshold: int = 40
    nginx_file_mask: str = r"nginx-access-ui\.log-(?P<date>\d{8})(\.gz)?$"

    def load_config_file(self, config_file: str = None):
        if config_file is None:
            return self
        try:
            with open(file=config_file, mode="r", encoding="UTF-8") as stream:
                json_config = json.load(fp=stream)
        except Exception as e:
            tb = sys.exception().__traceback__
            return e.with_traceback(tb)

        if not self.__dict__.__eq__(json_config):
            for key in json_config:
                self.__dict__[key] = json_config[key]

        return self