
import functools, types, templater

def path(p):
    def inner(f):
        setattr(f, 'path', p)
        return f
    return inner

@path('/hello')
def hello(req):
    target_page = 'hello'
    page = templater.render('templates/login_template.html', locals())
    return 'text/html', page, None

@path('/templates/style.css')
def style(req):
    f = open('templates/style.css', 'r')
    s = f.read()
    f.close()
    return 'text/css', s, None

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
