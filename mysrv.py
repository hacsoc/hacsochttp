"""Simple HTTP Server.

This module builds on BaseHTTPServer by implementing the standard GET
and HEAD requests in a fairly straightforward manner.

"""

import os, sys, thread, time, cgi, hashlib
import cookie_session, user_manager
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

    def __init__(self, module, *args, **kwargs):
        SocketServer.TCPServer.__init__(self, *args, **kwargs)
        self.module = module
        self.modfile = module.__file__[:-1] if module.__file__[-1] == 'c' else module.__file__
        print '-', self.modfile
        f = open(self.module.__file__, 'r')
        self.modhash = hashlib.md5(f.read()).digest()
        f.close()
        self.handlers = dict()
        self.sessions = safedict()
        self.users = safedict()
        self.users_email = safedict()
        self.applications = safedict()
        self.applications_name = safedict()
        self.applications_usrid = safedict()

    def reload(self):
        f = open(self.modfile, 'r')
        modhash = hashlib.md5(f.read()).digest()
        f.close()
        if modhash != self.modhash:
            print 'reloading'
            self.module = reload(module)
            self.modhash = modhash

    #def register_handlers(self, handlers):
        #self.handlers.update(handlers)
        #print self.handlers

    def handler(self, path):
        self.reload()
        def default(req, params): return None, None, None
        if path in self.module.handlers:
            #print self.handlers[path]
            return self.module.handlers[path]
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

    def __init__(self, *args, **kwargs):
        BaseHTTPServer.BaseHTTPRequestHandler.__init__(self, *args, **kwargs)
        self.session = dict()
        self.user = dict()

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
        if not hasattr(self, '_cookies'):
            if 'Cookie' not in self.headers: return dict()
            d = dict()
            for c in (cook.strip() for cook in self.headers['Cookie'].split(';')):
                k, v = c.split('=')
                d[k] = v
            self._cookies = d
        return self._cookies

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
        params = dict(params)
        print
        #print dict(self.server.users)
        #print dict(self.server.users_email)
        print self.client_address[0]
        print self.headers['User-Agent']
        print '"%s"' % self.path
        print path, params
        print self.cookies()
        try:
            cookie, ses_dict, user_dict = user_manager.init_session(self, params)
        except user_manager.LoginError, e:
            path = '/error'
            self.error = e.usrmsg
            content_type, page, cookies = self.server.handler(path)(self, params)
            _200(self, content_type, page, cookies)
            return
        self.session = ses_dict
        self.user = user_dict
        #print '...........................'
        #print cookie
        #print ses_dict
        #print user_dict
        #print '...........................'
        content_type, page, cookies = self.server.handler(path)(self, params)
        if cookies: cookies.append(cookie)
        else: cookies = [cookie]
        if page == None: _404(self)
        else: _200(self, content_type, page, cookies)

    def parseparams(self, params):
        return cgi.parse_qsl(params)
        #params = params.split('&')
        #d = dict()
        #for p in params:
            #p = p.split('=', 1)
            #if len(p) == 1: d.update({p[0]:''})
            #else: d.update({p[0]:p[1]})
        #return d

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
    if len(sys.argv) < 2:
        print 'you must supply the module you wish to serve'
        sys.exit(1)
    if len(sys.argv) == 3:
        l = sys.argv[2].split(':')
        for path in l:
            path = os.path.abspath(path)
            sys.path.append(path)
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
    httpd = HTTPServer(module, ("", PORT), Handler)
    #httpd.register_handlers(module.handlers)
    user_manager.add_user(httpd, '001', 'Tim Henderson', 'tim.tadh@gmail.com', 'test')
    print "serving at port", PORT
    thread.start_new_thread(httpd.serve_forever, tuple())
    raw_input('> enter to quit\n')
    httpd.shutdown()
    httpd.server_close()
    if hasattr(module, 'quithook'): module.quithook()
