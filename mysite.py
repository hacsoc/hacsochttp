
import functools, types, templater, cookie_session

def path(p):
    def inner(f):
        setattr(f, 'path', p)
        return f
    return inner

@path('/main')
def main(req, params):
    if req.user:
        user_id = req.user['usr_id']
        session_id = req.session['session_id']
        page = templater.render('templates/main.html', locals())
        return 'text/html', page, None
    else:
        return login(req, params)

@path('/coversheet')
def coversheet(req, params):
    if req.user:
        user_id = req.user['usr_id']
        session_id = req.session['session_id']
        page = templater.render('templates/coversheet.html', locals())
        return 'text/html', page, None
    else:
        return login(req, params)

@path('/applications')
def applications(req, params):
    def addapp(params):
        name = templater.cleaner.clean(params['name'])
        if name in req.server.applications_name:
            req.error = 'Application %s already begun' % (name)
            return error(req, params)
        appid = cookie_session.new_session_id()
        req.server.applications[appid] = {'name':name, 'appid':appid}
        req.server.applications_name[name] = appid
        if req.user['usr_id'] not in req.server.applications_usrid:
            req.server.applications_usrid[req.user['usr_id']] = list()
        req.server.applications_usrid[req.user['usr_id']].append(appid)
    if req.user:
        if 'name' in params: addapp(params)

        if req.user['usr_id'] not in req.server.applications_usrid:
            applications = list()
        else:
            applications = [req.server.applications[appid]
                   for appid in req.server.applications_usrid[req.user['usr_id']]]
        user_id = req.user['usr_id']
        session_id = req.session['session_id']
        page = templater.render('templates/applications.html', locals())
        return 'text/html', page, None
    else:
        return login(req, params)

@path('/login')
def login(req, params):
    target_page = 'main'
    session_id = req.session['session_id']
    page = templater.render('templates/login_template.html', locals())
    return 'text/html', page, None

@path('/templates/style.css')
def style(req, params):
    f = open('templates/style.css', 'r')
    s = f.read()
    f.close()
    return 'text/css', s, None

@path('/error')
def error(req, params):
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
