#!/usr/bin/python

#Programmer: Tim Henderson
#Contact: timothy.henderson@case.edu
#Case Western Reserve University
#Purpose: Functions for dealing with users

import os, time, sys
from Crypto.Hash import SHA256
import templater
import auth
import cookie_session

HOST = "localhost"
PORT = 3306
USER = 'diplomacy'
PASSWD = "d!plomacy12"
DB = "diplomacy"

class DBError(Exception): pass
class LoginError(Exception):
    def __init__(self, *args, **kwargs):
        super(LoginError, self).__init__(*args)
        self.usrmsg = kwargs['usrmsg']

def gen_userID():
    '''Generates exactly one userID using random information from /dev/urandom and the SHA256 hash
    algorithm.'''
    sha = SHA256.new()
    sha.update(os.urandom(64))
    for x in range(50):
        sha.update(sha.digest())
    return sha.hexdigest()

def make_user_dict(user_id, name, email, passwd, salt, last_login, creation, status):
    '''Makes a dictionary from the passed in parameters. Used to make sure the user_dicts returned by
    several functions are standard across the entire module.'''
    return {'usr_id':user_id, 'name':name, 'email':email, 'pass_hash':passwd, 'salt':salt,
            'last_login':last_login, 'creation':creation, 'status':status}

def get_user_byemail(req, email):
    '''Gets the user information for the user with the name passed in the parameter user_name. Returns
    the information as a dictionary.'''
    if email in req.server.users_email:
        return get_user_byid(req, req.server.users_email[email])
    return dict()

def get_user_byid(req, usr_id):
    '''Gets the user information for the user with the id passed in the parameter user_id. Returns
    the information as a dictionary.'''
    if usr_id in req.server.users:
        return dict(req.server.users[usr_id])
    return dict()

def update_last_login_time(req, usr_id):
    '''Updates the users table. Specifically the row where user_id matches the user_id passed into
    this function. It only updates one column (last_login) in the users table with the current time.'''
    if usr_id in req.server.users:
        user = dict(req.server.users[usr_id])
        user['last_login'] = time.strftime('%Y-%m-%d %H:%M:%S')
        req.server.users[usr_id] = user
        return dict(req.server.users[usr_id])
    return dict()

def add_user(srv, usr_id, name, email, password):
    '''Creates a new row in the user table with the passed in parameters and the current time.'''

    salt = auth.normalize(os.urandom(32))
    pass_hash = auth.saltedhash_hex(password, salt)
    srv.users[usr_id] = {
        'usr_id': usr_id,
        'name':name,
        'email':email,
        'pass_hash':pass_hash,
        'salt':salt,
        'last_login':time.strftime('%Y-%m-%d %H:%M:%S'),
        'creation':time.strftime('%Y-%m-%d %H:%M:%S'),
    }
    srv.users_email[email] = usr_id
    return dict(srv.users[usr_id])

def logout_session(req):
    c, ses_dict = cookie_session.init_session(req)
    session_id = ses_dict['session_id']
    if session_id in req.server.sessions:
        del req.server.sessions[session_id]

def verify_passwd(req, email, password):
    '''this takes the user_name (ie the string the user uses to log-in with) if and the plain text
    password. The password is hashed if there is a user by the name passed in then the hashes of the
    passwords are compared. If they match it returns True else it returns False.'''
    user_dict = get_user_byemail(req, email) #get the user_dict from the database
    if user_dict:
        pass_hash = auth.saltedhash_hex(password, user_dict['salt'])
    else:
        return False, dict()
    #if the user_dict actually has information in it check to see if the passwords are the same
    if user_dict and user_dict.has_key('pass_hash') and pass_hash == user_dict['pass_hash']:
        return True, user_dict #if they are return true and the user dictionary
    else:
        return False, dict() #else return false and an empty dictionary

def verify_login(req, form):
    '''This function takes a form or an empty dictionary.
    If the dictionary is empty it simply returns None. If there is no user by the name passed in it
    returns None. If the passwords do not match it returns None. If the username is valid and the
    password validates then it returns the user_id.'''
    usr_id = None #set a default value for the user_id
    if cookie_session.verify_session(req): # check to see if there is a valid session. you cannot
                                           # log in with out one.
        if form.has_key('email') and form.has_key('passwd'): # see if the correct form info got
                                                             # passed to the server
            try:
                email = templater.validators.Email(resolve_domain=True,
                                                 not_empty=True).to_python(form["email"])
            except templater.formencode.Invalid, e:
                raise LoginError("email did not pass validation: ", usrmsg="email: "+str(e))
            passwd = form['passwd'] #get the password
            valid, user_dict = verify_passwd(req, email, passwd) #verify the password and get the
                                                                 #user_dict as well

            if valid:
                usr_id = user_dict['usr_id'] #if it is valid grab the user_id from the user_dict
            else:
                raise LoginError("Password or email not correct.", usrmsg="Password or email not correct.")
        elif form.has_key('email') or form.has_key('passwd'):
            raise LoginError("All of the fields were not filled out.",
                    usrmsg="All fields must be filled out.")
    return usr_id

def init_session(req, form=None):
    '''Initiates a session using the cookie session module. If a form is passed in it trys to
    log the user in. The function will return a session dictionary and a user dictionary. If
    the current session has no user information associated with it the user dictionary will be
    empty. Note this function prints the header information, if you need to set custom cookies
    then you cannot currently use this function.'''
    if form is None: form = dict()

    usr_id = verify_login(req, form) #only actually gives you a user_id if you are logging in

    if usr_id is not None: #means you are logging in with good credentials
        update_last_login_time(req, usr_id) #so update the time
        # now invalidate the previous session
        logout_session(req)
        # make a new one
        c, ses_dict = cookie_session.make_new_session(req)
        ses_dict['usr_id'] = usr_id
        req.server.sessions[ses_dict['session_id']] = ses_dict
    else:
        # we are not logging in we just need to get the session
        # initializes the session returns the session dictionary and the cookie to push to browser
        c, ses_dict = cookie_session.init_session(req)

    user_id = ses_dict['usr_id'] #if you are logged in gives you the current user_id
    user_dict = get_user_byid(req, user_id) #get the user dictionary
    return c, ses_dict, user_dict
