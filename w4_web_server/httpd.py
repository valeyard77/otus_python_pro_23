import logging
import argparse

from multiprocessing import Process
from server import HttpServer

LOGGING_FORMAT = "[%(asctime)s] %(levelname).5s %(message)s"
LOGGING_DATE_FORMAT = "'%Y.%m.%d %H:%M:%S'"


def start_server(root_path):
    """ Create server instance and forever run it """
    server = HttpServer(document_root=root_path)
    server.run_forever()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Simple asynchronous web-server')
    parser.add_argument('--workers', '-w', type=int, help='Number of workers', default=4)
    parser.add_argument('--root_path', '-r', type=str, help='Root path of the documents')
    parser.add_argument("--logfile", dest="logfile", default=None)
    parser.add_argument("-X", "--debug", action="store_true", default=False, help="Enable debug mode")
    args = parser.parse_args()

    logging_level = logging.INFO if args.debug else logging.DEBUG
    logging.basicConfig(level=logging_level, format=LOGGING_FORMAT, datefmt=LOGGING_DATE_FORMAT, filename=args.logfile)

    document_root = args.root_path or None
    try:
        for _ in range(args.workers):
            p = Process(target=start_server, args=(document_root,))
            p.start()
    except KeyboardInterrupt:
        logging.info("Web Server terminated")
