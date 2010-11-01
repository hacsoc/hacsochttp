"""Simple HTTP Server.

This module builds on BaseHTTPServer by implementing the standard GET
and HEAD requests in a fairly straightforward manner.

"""

import os, sys
import posixpath
import BaseHTTPServer
import urllib
import cgi
import shutil
import mimetypes
import SocketServer
import time
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


mypage = """
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN"><html>
<title>some html yo</title>
<body>
<h1>Hello World!</h1>
</body>
</html>
"""

class SimpleHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    """Simple HTTP request handler with GET and HEAD commands.

    This serves files from the current directory and any of its
    subdirectories.  The MIME type for files is determined by
    calling the .guess_type() method.

    The GET and HEAD requests are identical except that the HEAD
    request omits the actual contents of the file.

    """

    server_version = "mysrv/0.0001"

    def head(self, content_type='text/html', content_len=0, cookies=None):
        self.send_response(200)
        self.send_header("Content-type", str(content_type))
        self.send_header("Content-Length", str(content_len))
        self.send_header("Last-Modified", self.date_time_string(time.time()))
        if cookies:
            for cookie in cookies:
                self.send_header("Set-Cookie", str(cookie))
                sys.stderr.write(str(cookie))
                sys.stderr.write('\n')
        self.end_headers()


    def do_GET(self):
        """Serve a GET request."""
        #s = self.rfile.read()
        if 'Cookie' in self.headers:
            sys.stderr.write("recieved = " + str(self.headers['Cookie']))
        self.head(content_len=len(mypage), cookies=["mycook=hello; expires=%s; path=/; HttpOnly" % (self.date_time_string(time.time()+30000))])
        self.wfile.write(mypage)

    def do_HEAD(self):
        """Serve a HEAD request."""
        self.head(content_len=len(mypage))

if __name__ == '__main__':
    PORT = 8000

    Handler = SimpleHTTPRequestHandler

    httpd = SocketServer.TCPServer(("", PORT), Handler)

    print "serving at port", PORT
    httpd.serve_forever()
