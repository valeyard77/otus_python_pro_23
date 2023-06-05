import argparse


class CliParser:
    nginx_logs_parser = argparse.ArgumentParser()
    nginx_logs_parser.add_argument('--config', action='store', help='Path to configuration file',
                                   required=False)
    nginx_logs_parser.add_argument('-X', '--debug', action='store_true', help='Set logging level',
                                   required=False)

    def __init__(self):
        self.nginx_logs_parser.parse_args(namespace=CliParser)

