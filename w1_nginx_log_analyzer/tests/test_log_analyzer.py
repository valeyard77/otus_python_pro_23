import sys
import os
import unittest
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import log_analyzer

logging.disable(logging.CRITICAL)


class TestCreateReport(unittest.TestCase):
    """ Procedure:
        1. Create test dict with url and time
        2. initiate control tuple - this tuple should be as a result of create_report func
        3. Run create_report function and get tuple created by this function
        ---------
        Verification:
        Compare two tuples. Should be exact match
    """

    def setUp(self):
        # generate test_time_log this dict is input for the tested function. Set report_size = 0
        self.test_report_size = 0
        self.test_time_log = {'url1': [50, 300, 200, 100, 250], 'url2': [100, 100, 100]}
        self.report_template = "app/resources/templates/report.html"
        self.report_filename = "./reports/report-2023.05.06.html"

        # generate control tuple with calculated statistic
        self.control_tuple = []

        sample = {"count": 5,
                  "time_avg": 180.0,
                  "time_max": 300.0,
                  "time_sum": 900.0,
                  "url": 'url1',
                  "time_med": 200.0,
                  "time_perc": 75.0,
                  "count_perc": 62.5
                  }
        self.control_tuple.append(sample)

        sample = {"count": 3,
                  "time_avg": 100.0,
                  "time_max": 100.0,
                  "time_sum": 300.0,
                  "url": 'url2',
                  "time_med": 100.0,
                  "time_perc": 25.0,
                  "count_perc": 37.5
                  }
        self.control_tuple.append(sample)

    def test_log_analyzer(self):
        total_requests_time = 0
        total_requests_count = 0
        for _, data in self.test_time_log.items():
            for v in data:
                total_requests_time += v
                total_requests_count += 1

        lfa = log_analyzer.LogAnalyzer()

        lfa.url_dict = self.test_time_log
        lfa.total_requests_time = total_requests_time
        lfa.total_requests_count = total_requests_count

        self.tuple_from_func = lfa.analyze_log_file()
        print(self.control_tuple)
        print(self.tuple_from_func)
        self.assertEqual(self.control_tuple, self.tuple_from_func)


if __name__ == '__main__':
    unittest.main()
