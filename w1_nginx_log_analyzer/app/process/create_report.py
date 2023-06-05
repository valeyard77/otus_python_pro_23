import json
import logging
import sys

from string import Template


class LogReport:
    def __init__(self, data: list, report_template: str, report_filename: str, report_size: int = None):
        self.data = data
        self.report_template = report_template
        self.report_filename = report_filename
        self.report_size = report_size

    def generate_report(self) -> bool:
        """Writes report of statistic data to file."""
        logging.debug(f"Writes report of statistic data to file {self.report_filename}")
        if self.report_size is None:
            report_size = len(self.data)
        if self.report_size < len(self.data):
            selected = sorted(self.data, key=lambda x: x['time_sum'], reverse=True)
            data = selected[:self.report_size]

        # converts floats to string for better view in report
        for d in self.data:
            d['time_med'] = round(d['time_med'], 3)
            d['time_perc'] = round(d['time_perc'], 3)
            d['time_avg'] = round(d['time_avg'], 3)
            d['count_perc'] = round(d['count_perc'], 3)
            d['time_sum'] = round(d['time_sum'], 3)

        json_data = json.dumps(self.data)

        try:
            with open(self.report_template, mode='r', encoding='utf-8') as tf:
                template = Template(tf.read())

            with open(self.report_filename, mode='w', encoding='utf-8') as rf:
                rf.write(template.safe_substitute(table_json=json_data))
        except Exception as e:
            exc = sys.exc_info()
            logging.error(f"an error occurred while generating the report file, {e}", exc_info=exc)
            return False

        return True
