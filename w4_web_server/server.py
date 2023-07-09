import os
import re
import socket
import logging
import datetime
import urllib.parse


class HttpServer:
    """ Base HTTP Server """

    HOST = 'localhost'
    PORT = 8000
    REQUEST_QUEUE_SIZE = 4096
    DOCUMENT_ROOT = 'httptest'
    COMMON_PATTERN = r'(?P<request>(GET|HEAD)) (?P<url>.+(\.(html|css|js|jpg|jpeg|png|gif|swf|txt|\/.*)||\w))\s+HTTP\/1.(\d)'
    CONTENT_TYPES = {
        'html': 'text/html',
        'css': 'text/css',
        'js': 'application/javascript',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'swf': 'application/x-shockwave-flash'
    }

    def __init__(self, **kwargs):
        """ Server constructor """

        self.host = kwargs.get('host', self.HOST)
        self.port = kwargs.get('port', self.PORT)
        self.document_root = kwargs.get('document_root', self.DOCUMENT_ROOT) or self.DOCUMENT_ROOT
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(self.REQUEST_QUEUE_SIZE)

    def run_forever(self):
        """ Run server forever """

        logging.info(f"[PID={os.getpid()}] Simple WEB Server start on http://{self.host}:{self.port}")
        try:
            while True:
                client_connection, client_address = self.socket.accept()
                try:
                    self.handle_request(client_connection)
                finally:
                    client_connection.close()
        finally:
            self.socket.close()

    def handle_request(self, client_connection):
        request = client_connection.recv(4096)
        logging.debug(f"PID=[{os.getpid()}] {request}")
        request_dict = self._parse_request_params(request)
        if not request_dict:
            content = 'Client\'s response is not correct'
            client_connection.send(self._http_status_response(status_code=400, content=content))
            return
        http_response = self._response(request_dict)
        try:
            client_connection.sendall(http_response)
        except ConnectionResetError:
            logging.warning(f'PID=[{os.getpid()}] Connection reset by peer')

    def _parse_request_params(self, req_str):
        """ Parse request string and return dictionary with attributes """

        try:
            request = str(
                req_str.decode('utf-8')
            ).replace('\n', ' ').replace('\r', '').strip()
            data = re.search(self.COMMON_PATTERN, request, re.IGNORECASE)
            if data and '../' not in request:
                return data.groupdict()
        except Exception as e:
            logging.error(f"PID=[{os.getpid()}] {e}", exc_info=e)
            return {'status': '405'}

    def _response(self, attrs):
        """ Make a response, based on attributes """
        try:
            if attrs.get('status') == '405':
                return self._http_status_response(status_code=405, content="Given method is not allowed")

            url = urllib.parse.unquote_plus((attrs.get('url').split('?')[0][1:]))
            if self.document_root in url:
                default_path = url
            else:
                default_path = os.path.join(self.document_root, url)
            if os.path.isfile(default_path):
                response = self._http_status_response(filepath=default_path, request=attrs)
            elif os.path.isdir(default_path):
                file_path = os.path.join(default_path, 'index.html')
                if not os.path.isfile(file_path):
                    content = f"Directory\'s file is abscent, file on path {file_path} does not exist"
                    response = self._http_status_response(status_code=503, content=content)
                else:
                    response = self._http_status_response(filepath=file_path, request=attrs)
            else:
                content = f"File on path {default_path} does not exist"
                response = self._http_status_response(status_code=404, content=content)

            return response
        except Exception as e:
            logging.error(f"PID=[{os.getpid()}] {e}", exc_info=e)
            return self._http_status_response(status_code=500, content=e)

    def _http_status_response(self, status_code=200, content=None, request=None, filepath=None):
        file_size = 0
        status_text = {
            200: "OK", 400: "Bad Request",
            404: "Not found", 405: "Method Not Allowed",
            500: "Internal Server Error",
            503: "Service Unavailable"
        }

        if status_code == 200:
            """ Return 200 response """
            supposed_format = filepath.split('.')[-1]

            format = supposed_format if supposed_format in self.CONTENT_TYPES.keys() else 'html'
            content_type = self.CONTENT_TYPES.get(format, 'text/html')
            file_size = os.path.getsize(filepath)

            with open(filepath, 'rb') as file_data:
                content = file_data.read().decode("utf-8") if content_type == "text/html" else file_data.read()

            return self._response_data(
                status=status_code,
                status_text=status_text[status_code],
                content_type=content_type,
                content=content,
                content_length=file_size,
                request_info=request
            )

        """ else return 4xx/5xx response codes"""
        return self._response_data(
            status=status_code,
            status_text=status_text.get(status_code, "unknown"),
            content=content
        )

    @staticmethod
    def _response_data(**kwargs):
        """ Base response method """

        content = kwargs.get('content', None)

        request_info = kwargs.get('request_info', {})
        date = str(datetime.datetime.now())
        response = f"HTTP/1.1 {kwargs.get('status', None)} {kwargs.get('status_text', None)}\r\n"
        response += f"Content-Type: {kwargs.get('content_type', 'text/html')}\r\n"
        if kwargs.get('content_length'):
            response += f"Content-Length: {kwargs.get('content_length')}\r\n"
        response += f"Date: {date}\r\n"
        response += "Server: my-server\r\n"
        response += "Connection: close\r\n\r\n"

        if request_info.get('request', None) != 'HEAD':
            response_bytes = response.encode("UTF-8") + (
                content if isinstance(content, bytes) else content.encode("UTF-8"))
        else:
            response_bytes = response.encode("UTF-8")

        return response_bytes
