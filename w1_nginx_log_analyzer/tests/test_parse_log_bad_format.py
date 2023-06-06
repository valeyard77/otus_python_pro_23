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
        The test should fail with an error 68% of the text is not parsed
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
            '1.99.174.176 3b81f63526fa8  - [29/Jun/2017:03:50:22 +0300] "GET /api/1/photogenic_banners/list/?server_name=WIN7RB4 HTTP/1.1" 200 12 "-" "Python-urllib/2.7" "-" "1498697422-32900793-4708-9752770" "-" 0.133',
            '1.169.137.128 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/16852664 HTTP/1.1" 200 19415 "-" "Slotovod" "-" "1498697422-2118016444-4708-9752769" "712e90144abee9" 0.199',
            'bad string',
            'bad string',
            'bad string',
            'bad string',
            'bad string',
            'bad string',
            'bad string',
            'bad string',
            'bad string',
            'bad string',
            'bad string',
            '1.199.4.96 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/slot/4705/groups HTTP/1.1" 200 2613 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" "1498697422-3800516057-4708-9752745" "2a828197ae235b0b3cb" 0.704',
            '1.168.65.96 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/internal/banner/24294027/info HTTP/1.1" 200 407 "-" "-" "-" "1498697422-2539198130-4709-9928846" "89f7f1be37d" 0.146',
            '1.169.137.128 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/group/1769230/banners HTTP/1.1" 200 1020 "-" "Configovod" "-" "1498697422-2118016444-4708-9752747" "712e90144abee9" 0.628'
        ]
        self.log_dir = os.path.abspath(test_folder)
        self.last_log = 'nginx-access-ui.log-20230605'
        self.log_file_path = os.path.join(self.log_dir, self.last_log)
        with open(self.log_file_path, mode='w') as file:
            for line in self.test_lines:
                file.write(line+'\n')

    def test_parse_log(self):
        self.dict_from_func = log_analyzer.LogAnalyzer(error_threshold=10).find_last_log_file(nginx_logs_dir=self.log_dir).parse_log_file().url_dict
        print(self.dict_from_func)


    def tearDown(self):
            # Remove test logfile after the test
            print('Remove test logfile after the test')
            os.remove(self.log_file_path)
            os.rmdir(self.log_dir)


if __name__ == '__main__':
    unittest.main()