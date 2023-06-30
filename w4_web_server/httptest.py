#!/usr/bin/env python

import re
import socket
import http.client as hc
import unittest


class HttpServer(unittest.TestCase):
    host = "localhost"
    port = 8000

    def setUp(self):
        self.conn = hc.HTTPConnection(self.host, self.port, timeout=10)

    def tearDown(self):
        self.conn.close()

    def test_empty_request(self):
        """ Send bad http headers """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        s.sendall("\n".encode("utf-8"))
        s.close()

    def test_server_header(self):
        """Server header exists"""
        self.conn.request("GET", "/httptest/")
        r = self.conn.getresponse()
        data = r.read()
        server = r.getheader("Server")
        self.assertIsNotNone(server)

    def test_directory_index(self):
        """directory index file exists"""
        self.conn.request("GET", "/httptest/dir2/")
        r = self.conn.getresponse()
        data = r.read()
        length = r.getheader("Content-Length")
        self.assertEqual(int(r.status), 200)
        self.assertEqual(int(length), 55)
        self.assertEqual(len(data), 55)
        self.assertEqual(data.decode("utf-8"), "<html><body><h1>Directory index file</h1></body></html>")

    def test_index_not_found(self):
        """directory index file absent"""
        self.conn.request("GET", "/httptest/dir1/")
        r = self.conn.getresponse()
        data = r.read()
        self.assertEqual(int(r.status), 403)

    def test_file_not_found(self):
        """absent file returns 404"""
        self.conn.request("GET", "/httptest/smdklcdsmvdfjnvdfjvdfvdfvdsfssdmfdsdfsd.html")
        r = self.conn.getresponse()
        data = r.read()
        self.assertEqual(int(r.status), 404)

    def test_file_in_nested_folders(self):
        """file located in nested folders"""
        self.conn.request("GET", "/httptest/dir1/dir12/dir123/file.txt")
        r = self.conn.getresponse()
        data = r.read()
        length = r.getheader("Content-Length")
        self.assertEqual(int(r.status), 200)
        self.assertEqual(int(length), 24)
        self.assertEqual(len(data), 24)
        self.assertEqual(data.decode("utf-8"), "ai-forever/ruBert-large\n")

    def test_file_with_query_string(self):
        """slash after filename"""
        self.conn.request("GET", "/httptest/dir2/page.html/")
        r = self.conn.getresponse()
        data = r.read()
        self.assertEqual(int(r.status), 404)

    def test_file_with_query_string2(self):
        """query string after filename"""
        self.conn.request("GET", "/httptest/dir2/page.html?arg1=value&arg2=value")
        r = self.conn.getresponse()
        data = r.read()
        length = r.getheader("Content-Length")
        self.assertEqual(int(r.status), 200)
        self.assertEqual(int(length), 37)
        self.assertEqual(len(data), 37)
        self.assertEqual(data.decode("utf-8"), "<html><body>Page Sample</body></html>")

    def test_file_with_spaces(self):
        """filename with spaces"""
        self.conn.request("GET", "/httptest/lorem%20ipsum.txt")
        r = self.conn.getresponse()
        data = r.read()
        length = r.getheader("Content-Length")
        self.assertEqual(int(r.status), 200)
        self.assertEqual(int(length), 445)
        self.assertEqual(len(data), 445)
        self.assertTrue(data.decode("utf-8").__contains__("Lorem ipsum dolor"))

    def test_file_urlencoded(self):
        """urlencoded filename"""
        self.conn.request("GET", "/httptest/dir2/%70%61%67%65%2e%68%74%6d%6c")
        r = self.conn.getresponse()
        data = r.read()
        length = r.getheader("Content-Length")
        self.assertEqual(int(r.status), 200)
        self.assertEqual(int(length), 37)
        self.assertEqual(len(data), 37)
        self.assertEqual(data.decode("utf-8"), "<html><body>Page Sample</body></html>")

    def test_document_root_escaping(self):
        """document root escaping forbidden"""
        self.conn.request("GET", "/httptest/../../../../../../../../../../../../../etc/passwd")
        r = self.conn.getresponse()
        data = r.read()
        self.assertIn(int(r.status), (400, 403, 404))

    def test_post_method(self):
        """post method forbidden"""
        self.conn.request("POST", "/httptest/dir2/page.html")
        r = self.conn.getresponse()
        data = r.read()
        self.assertIn(int(r.status), (400, 405))

    def test_head_method(self):
        """head method support"""

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        s.send("HEAD /httptest/dir2/page.html HTTP/1.0\r\n\r\n".encode("Utf-8"))
        data = ""
        while 1:
            buf = s.recv(1024)
            if not buf:
                break
            data += buf.decode("utf-8")
        s.close()

        self.assertTrue(data.find("\r\n\r\n") > 0, "no empty line with CRLF found")
        (head, body) = re.split("\r\n\r\n", data, 1)
        headers = head.split("\r\n")
        self.assertTrue(len(headers) > 0, "no headers found")
        statusline = headers.pop(0)
        (proto, code, status) = statusline.split(" ")
        h = {}
        for k, v in enumerate(headers):
            name, value = re.split(r'\s*:\s*', v, 1)
            h[name] = value
        if int(code) == 200:
            self.assertEqual(int(h['Content-Length']), 37)
            self.assertEqual(len(body), 0)
        else:
            self.assertIn(int(code), (400, 405))

    def test_filetype_html(self):
        """Content-Type for .html"""
        self.conn.request("GET", "/httptest/dir2/page.html")
        r = self.conn.getresponse()
        data = r.read()
        length = r.getheader("Content-Length")
        ctype = r.getheader("Content-Type")
        self.assertEqual(int(r.status), 200)
        self.assertEqual(int(length), 37)
        self.assertEqual(len(data), 37)
        self.assertEqual(ctype, "text/html")

    def test_filetype_jpg(self):
        """Content-Type for .jpg"""
        self.conn.request("GET", "/httptest/image.jpg")
        r = self.conn.getresponse()
        data = r.read()
        length = r.getheader("Content-Length")
        ctype = r.getheader("Content-Type")
        self.assertEqual(int(r.status), 200)
        self.assertEqual(int(length), 514262)
        self.assertEqual(len(data), 514262)
        self.assertEqual(ctype, "image/jpeg")

    def test_filetype_jpeg(self):
        """Content-Type for .jpeg"""
        self.conn.request("GET", "/httptest/image2.jpeg")
        r = self.conn.getresponse()
        data = r.read()
        length = r.getheader("Content-Length")
        ctype = r.getheader("Content-Type")
        self.assertEqual(int(r.status), 200)
        self.assertEqual(int(length), 420351)
        self.assertEqual(len(data), 420351)
        self.assertEqual(ctype, "image/jpeg")

    def test_filetype_png(self):
        """Content-Type for .png"""
        self.conn.request("GET", "/httptest/map.png")
        r = self.conn.getresponse()
        data = r.read()
        length = r.getheader("Content-Length")
        ctype = r.getheader("Content-Type")
        self.assertEqual(int(r.status), 200)
        self.assertEqual(int(length), 42656)
        self.assertEqual(len(data), 42656)
        self.assertEqual(ctype, "image/png")

    def test_filetype_gif(self):
        """Content-Type for .gif"""
        self.conn.request("GET", "/httptest/douluo.gif")
        r = self.conn.getresponse()
        data = r.read()
        length = r.getheader("Content-Length")
        ctype = r.getheader("Content-Type")
        self.assertEqual(int(r.status), 200)
        self.assertEqual(int(length), 3256503)
        self.assertEqual(len(data), 3256503)
        self.assertEqual(ctype, "image/gif")


loader = unittest.TestLoader()
suite = unittest.TestSuite()
a = loader.loadTestsFromTestCase(HttpServer)
suite.addTest(a)


class NewResult(unittest.TextTestResult):
    def getDescription(self, test):
        doc_first_line = test.shortDescription()
        return doc_first_line or ""


class NewRunner(unittest.TextTestRunner):
    resultclass = NewResult


if __name__ == '__main__':
    runner = NewRunner(verbosity=2)
    runner.run(suite)
