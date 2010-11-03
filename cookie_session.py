#!/usr/bin/python

#Programmer: Tim Henderson
#Contact: timothy.henderson@case.edu
#Case Western Reserve University
#Purpose: Functions for dealing with session cookies

import os, time, hmac
from hashlib import sha256 as SHA256
#from logger import Logger
#logger = Logger(__file__)

HOST = "masran.case.edu"
PORT = 3306
USER = 'diplomacy'
PASSWD = "d!plomacy12"
DB = "diplomacy"

class DBError(Exception): pass

#time.strftime('%Y-%m-%d %H:%M:%S')

count = 0

def new_session_id(prounds=50):
    '''Generates a new sessionID based on the seed, some random information from /dev/urandom and the
    current time since the epoch.'''
    randata = os.urandom(32)
    sha = SHA256()
    sha.update(randata)
    sha.update(str(time.time()))
    for x in range(prounds):
        sha.update(sha.digest())
    return sha.hexdigest()

def sign_msg(sigid, time, ip_addr, usragent, msg):
    '''Signs a msg using the passed in parameters.'''
    print '--->', sigid, time, ip_addr, usragent, msg
    shamac = hmac.new(sigid, '', SHA256)
    shamac.update(msg)
    shamac.update(ip_addr)
    shamac.update(str(time))
    shamac.update(usragent)
    for x in range(1000):
        shamac.update(shamac.digest())
    return shamac.hexdigest()

def new_sig_id():
    '''Generates a new and random signatureID used for signing cookies.'''
    sha = SHA256()
    sha.update(os.urandom(64))
    for x in range(100):
        sha.update(sha.digest())
    return sha.hexdigest()

def create_cookie(req, session_id, sig_id, time_signed):
    '''Creates a cookie from the passed in parameters and signs it with the sigID and returns the
    cookie and the msg_sig.'''
    msg_sig = sign_msg(sig_id, time_signed, req.client_address[0], req.headers['User-Agent'], session_id)
    cookie = req.make_cookie('timsession', session_id)
    return cookie, msg_sig

def check_cookie(req, sig, sig_id, time_signed, msg):
    '''Checks to see if the cookie is valid from the passed in parameters. sig is the signature of
    the cookie that was saved in the database. SignatureID is the ID used to sign the cookie. time_signed
    is the time since the epoch that the cookie was signed and the msg is of course what was actually
    signed. Returns True if the cookie is valid, False otherwise.'''

    sig2 = sign_msg(sig_id, time_signed, req.client_address[0], req.headers['User-Agent'], msg)
    print '------------'
    print sig
    print sig2
    print '------------'
    if sig2 == sig: return True
    else: return False

def create_session(req, session_id, sig_id, msg_sig, usr_id, time_signed):
    '''Creates a new row in the session table with the passed in parameters and the current time.'''
    d = {
        'session_id':session_id,
        'sig_id':sig_id,
        'msg_sig':msg_sig,
        'usr_id':usr_id,
        'time':time_signed,
        'ip_addr':req.client_address[0],
        'usr_agent':req.headers['User-Agent']
    }
    req.server.sessions[session_id] = d
    return d

def update_session(req, session_id, sig_id, msg_sig, usr_id, time_signed):
    '''Updates the session identified by the session ID, with passed in parameters and the current
    time.'''
    if session_id in req.server.sessions:
        session = dict(req.server.sessions[session_id])
        session['sig_id'] = sig_id
        session['msg_sig'] = msg_sig
        session['usr_id'] = usr_id
        session['time'] = time_signed
        req.server.sessions[session_id] = session
    return get_session(req, session_id)

def get_session(req, session_id):
    '''Get the session from the session table in the database identified by the sessionID. It returns
    the session in the session dictionary format.'''
    if session_id in req.server.sessions:
        return dict(req.server.sessions[session_id])
    return dict()

def clear_old_sessions(req):
    '''This method goes through all the rows in in the table session and checks to see if they have
    expire or if there are duplicates. If either is the case it deletes them from the table.'''
    todel = list()
    ctime = time.time()
    for session_id, session in req.server.sessions.iteritems():
        if session['time'] + 2000 < ctime:
            todel.append(session_id)
    for session_id in todel:
        delete_session(req, session_id)


def delete_session(req, session_id):
    '''This removes the session identified by its sessionID from the database in the table session'''
    if session_id in req.server.sessions:
        del req.server.sessions[session_id]

def make_new_session(req):
    '''This creates a new session. This means it creates a new row in the session table of the database.
    It also generates a session cookie for the new session. The function returns the cookie and the
    session dictionary.'''
    sig_id = new_sig_id()
    session_id = new_session_id()
    epochtime = time.time()
    c, msg_sig = create_cookie(req, session_id, sig_id, epochtime)
    ses_dict = create_session(req, session_id, sig_id, msg_sig, 'unknown', epochtime)
    return c, ses_dict

def init_session(req, user=None):
    '''Initiates the session. Before trying to validate
    the session and generating a new session cookie the function first calls clear_old_sessions(),
    ensuring only non-expired sessions are validated. If the session validates then it generates
    a new session cookie for that session. If anything else happens it creates a new session and
    generates a new cookie. The method returns the generated cookie and the session dictionary.'''
    clear_old_sessions(req)
    cookies = req.cookies()
    ses_dict = {}
    if cookies.has_key('timsession'):

        session_id = cookies['timsession']
        session = get_session(req, session_id)
        if session:
            cookie_check = check_cookie(req, session['msg_sig'],
                                session['sig_id'], session['time'], session_id)
        else:
            cookie_check = None
        if cookie_check:
            sig_id = new_sig_id()
            epochtime = time.time()
            if user == None: user = session['usr_id']
            c, msg_sig = create_cookie(req, session['session_id'], sig_id, epochtime)
            ses_dict = update_session(req, session['session_id'], sig_id, msg_sig, user, epochtime)
        else:
            c, ses_dict = make_new_session(req)
    else:
        c, ses_dict = make_new_session(req)
    return c, ses_dict

def verify_session(req):
    '''This method returns True if the current session is valid, False otherwise.'''
    cookies = req.cookies()
    if cookies.has_key('timsession'):
        session_id = cookie['timsession']
        session = get_session(session_id)
        if session:
            return check_cookie(req, session['msg_sig'],
                                session['sig_id'], session['time'], session_id)
    return False
