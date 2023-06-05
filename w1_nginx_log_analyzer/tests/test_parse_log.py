import sys
import os
import logging
import unittest

logging.disable(logging.CRITICAL)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import log_analyzer

class TestParseLog(unittest.TestCase):

    """ Procedure:
        1. Create test file for parsing in './test_folder' dir. This file mimics structure of real log files
        2. Initiate control dict - this dict should be as a result of testing file
        3. Run parse_log_file function from LogAnalyzer class and get dict created by this function

        Verification:
        Compare two dicts. Should be exact match
    """

    def setUp(self):
        # generate test file with 2 test lines. Real data were obfuscated
        test_folder = "./test_folder"
        try:
            os.mkdir(test_folder)
            print(f"make directory {test_folder}")
        except:
            pass

        self.test_lines = [
            '1.19.32 -  - [29/Jun +0300] "GET /api/v2/ HTTP/1.1" 200 927 "-" "Lynx/2 libw GNU" "-" "149" "dc" 0.466',
            '1.99.17 3b88  - [29/Ju +0300] "GET /api/v1/ HTTP/1.1" 200 12 "-" "Python-urllib/2.7" "-" "14970" "-" 0.146'
        ]
        self.log_dir = os.path.abspath(test_folder)
        self.last_log = 'nginx-access-ui.log-20230605'
        self.log_file_path = os.path.join(self.log_dir, self.last_log)
        with open(self.log_file_path, mode='w') as file:
            for line in self.test_lines:
                file.write(line+'\n')
        self.control_dict = {'/api/v2/':  [0.466], '/api/v1/': [0.146]}

    def test_parse_log(self):
        self.dict_from_func = log_analyzer.LogAnalyzer().find_last_log_file(nginx_logs_dir=self.log_dir).parse_log_file().url_dict
        print(self.dict_from_func)
        print(self.control_dict)

        self.assertDictEqual(self.control_dict, self.dict_from_func)

    def tearDown(self):
            # Remove test logfile after the test
            print('Remove test logfile after the test')
            os.remove(self.log_file_path)
            os.rmdir(self.log_dir)


if __name__ == '__main__':
    unittest.main()