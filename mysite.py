
import functools, types, templater

def path(p):
    def inner(f):
        setattr(f, 'path', p)
        return f
    return inner

@path('/main')
def main(req):
    if req.user:
        user_id = req.user['usr_id']
        session_id = req.session['session_id']
        page = templater.render('templates/main.html', locals())
        return 'text/html', page, None
    else:
        return login(req)

@path('/login')
def login(req):
    target_page = 'main'
    session_id = req.session['session_id']
    page = templater.render('templates/login_template.html', locals())
    return 'text/html', page, None

@path('/templates/style.css')
def style(req):
    f = open('templates/style.css', 'r')
    s = f.read()
    f.close()
    return 'text/css', s, None

@path('/error')
def error(req):
    if hasattr(req, 'error'): error = str(req.error)
    else: error = 'no error?'
    page = templater.render('templates/error.html', locals())
    return 'text/html', page, None

#print hello
#print hello.path
#print hello(0)
#print type(hello), isinstance(hello, types.FunctionType)
#print

handlers = dict()
for obj in dict(locals()).itervalues():
    #print obj, hasattr(obj, 'path')
    if hasattr(obj, 'path') and isinstance(obj, types.FunctionType):
        handlers[obj.path] = obj

#print
#print handlers['/hello']('')
