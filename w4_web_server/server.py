import os
import re
import socket
import logging
import datetime
import urllib.parse


class HttpServer(object):
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

        logging.info(f"[PID={os. getpid()}] Simple WEB Server start on http://{self.host}:{self.port}")
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
            client_connection.send(self._wrong_client_response())
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
            logging.error(f"PID=[{os. getpid()}] {e}", exc_info=e)
            return {'status': '405'}

    def _response(self, attrs):
        """ Make a response, based on attributes """
        try:
            if attrs.get('status') == '405':
                return self._405_response()

            url = urllib.parse.unquote_plus((attrs.get('url').split('?')[0][1:]))
            if self.document_root in url:
                default_path = url
            else:
                default_path = os.path.join(self.document_root, url)
            if os.path.isfile(default_path):
                response = self._200_response(default_path, attrs)
            elif os.path.isdir(default_path):
                file_path = os.path.join(default_path, 'index.html')
                if not os.path.isfile(file_path):
                    content = f"File on path {file_path} does not exist"
                    response = self._directory_file_abscent(content)
                else:
                    response = self._200_response(file_path, attrs)
            else:
                content = f"File on path {default_path} does not exist"
                response = self._404_response(content)

            return response
        except Exception as e:
            logging.error(f"PID=[{os. getpid()}] {e}", exc_info=e)
            return self._500_response(e)

    def _200_response(self, filepath, request=None):
        """ Return 200 response """

        supposed_format = filepath.split('.')[-1]

        format = supposed_format if supposed_format in self.CONTENT_TYPES.keys() else 'html'
        content_type = self.CONTENT_TYPES.get(format, 'text/html')
        file_size = os.path.getsize(filepath)
        file_data = open(filepath, 'rb')
        content = file_data.read().decode("utf-8") if content_type == "text/html" else file_data.read()
        response = self._response_data(
            status=200, status_text='OK',
            content_type=content_type, content_length=file_size,
            content=content, request_info=request
        )
        file_data.close()
        return response

    def _404_response(self, message):
        """ Return 404 response """

        return self._response_data(
            status=404, status_text='Not found',
            content=message
        )

    def _405_response(self):
        """ Return 405 response """

        return self._response_data(
            status=405, status_text='Method Not Allowed',
            content='Given method is not allowed'
        )

    def _500_response(self, error):
        """ Return 500 error """

        return self._response_data(
            status=500, status_text='Internal Server Error',
            content='Server error'
        )

    def _wrong_client_response(self):
        """ Return response if the client request is incorrect """

        return self._response_data(
            status=400, status_text='Service Unavailable',
            content='Client\'s response is not correct'
        )

    def _directory_file_abscent(self, content):
        """ Return response if directory index file is abscent """

        return self._response_data(
            status=403, status_text='Service Unavailable',
            content=f'Directory\'s file is abscent, {content}'
        )

    def _response_data(self, **kwargs):
        """ Base response method """

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
            response += f"{kwargs.get('content', None)}"

        return response.encode("utf-8")
