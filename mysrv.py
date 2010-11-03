"""Simple HTTP Server.

This module builds on BaseHTTPServer by implementing the standard GET
and HEAD requests in a fairly straightforward manner.

"""

import os, sys, thread, time, cookie_session
import BaseHTTPServer, SocketServer
from safedict import ThreadSafeDict as safedict
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


#mypage = """
#<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN"><html>
#<title>some html yo</title>
#<body>
#<h1>Hello World!</h1>
#</body>
#</html>
#"""

#writer locking:
    #aquire  wrtlock
    #do write
    #release wrtlock

#reader locking:
    #aquire mutex
    #rdcount += 1
    #if rdcount == 1: aquire wrtlock
    #release mutex

    #do read

    #aquire mutex
    #rdcount -= 1
    #if rdcount == 0: release wrtlock
    #release mutex

class HTTPServer(SocketServer.TCPServer):

    def __init__(self, *args, **kwargs):
        SocketServer.TCPServer.__init__(self, *args, **kwargs)
        self.handlers = dict()
        self.sessions = safedict()
        self.users = safedict()
        self.users_email = safedict()

    def register_handlers(self, handlers):
        self.handlers.update(handlers)
        print self.handlers

    def handler(self, path):
        def default(req): return None, None, None
        if path in self.handlers:
            #print self.handlers[path]
            return self.handlers[path]
        return default


class SimpleHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    """Simple HTTP request handler with GET and HEAD commands.

    This serves files from the current directory and any of its
    subdirectories.  The MIME type for files is determined by
    calling the .guess_type() method.

    The GET and HEAD requests are identical except that the HEAD
    request omits the actual contents of the file.

    """

    server_version = "mysrv/0.0001"

    def head(self, response_code=200, content_type='text/html', content_len=0, cookies=None):
        self.send_response(response_code)
        self.send_header("Content-type", str(content_type))
        self.send_header("Content-Length", str(content_len))
        self.send_header("Last-Modified", self.date_time_string(time.time()))
        if cookies:
            for cookie in cookies:
                self.send_header("Set-Cookie", str(cookie))
                sys.stderr.write(str(cookie))
                sys.stderr.write('\n')
        self.end_headers()

    def make_cookie(self, key, value, path='/', httponly=True):
        ## security vulnerabilities in this function can you spot them?
        if httponly: httponly = 'HttpOnly'
        else: httponly = ''
        expires = self.date_time_string(time.time()+30000)
        c="%s=%s; expires=%s; path=%s; %s"%(key, value, expires, path, httponly)
        return c

    def cookies(self):
        if 'Cookie' not in self.headers: return dict()
        d = dict()
        for c in (cook.strip() for cook in self.headers['Cookie'].split(';')):
            k, v = c.split('=')
            d[k] = v
        return d

    def do(self, path, params):
        def _404(req):
            page = '''
            <!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN"><html>
            <title>404 Page Not Found</title>
            <body>
            <h1>404 Page Not Found</h1>
            </body>
            </html>
            '''
            req.head(response_code=404, content_len=len(page))
            req.wfile.write(page)
        def _200(req, content_type, page, cookies):
            self.head(content_len=len(page), content_type=content_type, cookies=cookies)
            self.wfile.write(page)
        print
        print self.client_address[0]
        print self.headers['User-Agent']
        print '"%s"' % self.path
        print path, params
        print self.cookies()
        cookie, ses_dict = cookie_session.init_session(self)
        print cookie
        #print ses_dict
        content_type, page, cookies = self.server.handler(path)(self)
        if cookies: cookies.append(cookie)
        else: cookies = [cookie]
        if page == None: _404(self)
        else: _200(self, content_type, page, cookies)

    def parseparams(self, params):
        params = params.split('&')
        d = dict()
        for p in params:
            p = p.split('=', 1)
            if len(p) == 1: d.update({p[0]:''})
            else: d.update({p[0]:p[1]})
        return d

    def parsepath(self, p):
        split = self.path.split('?', 1)
        if len(split) == 1: return split[0], dict()
        else: return split[0], self.parseparams(split[1])

    def do_GET(self):
        """Serve a GET request."""
        #s = self.rfile.read()
        #self.head(content_len=len(mypage), cookies=["mycook=hello; expires=%s; path=/; HttpOnly" % (self.date_time_string(time.time()+30000))])
        #self.wfile.write(mypage)
        path, params = self.parsepath(self.path)
        self.do(path, params)

    def do_POST(self):
        path, params = self.parsepath(self.path)
        post_params = self.rfile._rbuf.getvalue()
        print 'post params = %s' % post_params
        params.update(self.parseparams(post_params))
        self.do(path, params)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print 'you must supply the module you wish to serve'
        sys.exit(1)
    module = __import__(sys.argv[1])
    print module
    print hasattr(module, 'handlers')
    if not hasattr(module, 'handlers'):
        print 'module cannot be served because it does not have a handlers attr'
        sys.exit(2)
    print module.handlers
    PORT = 8000
    Handler = SimpleHTTPRequestHandler
    HTTPServer.allow_reuse_address = True
    httpd = HTTPServer(("", PORT), Handler)
    httpd.register_handlers(module.handlers)
    print "serving at port", PORT
    thread.start_new_thread(httpd.serve_forever, tuple())
    raw_input('> enter to quit\n')
    httpd.shutdown()
    httpd.server_close()
