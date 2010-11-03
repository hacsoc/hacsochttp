import os, re, yaptu, sys
#import warnings
#warnings.simplefilter('ignore', UserWarning)
import formencode
from formencode import validators
#warnings.simplefilter('default', UserWarning)
import string
import base64
try: import cStringIO as strio
except ImportError: import StringIO as strio

__rex = re.compile('\<\%([^\<\%]+)\%\>')
__rbe = re.compile('\s*\<\+')
__ren = re.compile('\s*\-\>')
__rco = re.compile('\s*\|= ')

__templater_namespace = locals()
#validators.MaxLength

class Text(formencode.FancyValidator):
    '''
    The swiss army knife of dealing with textual input from the user. Using as a validator goes like
    this:
        clean_base64_text = Text(256).to_python(text)
        clean_text = Text().from_python(clean_base64_text)
    If you want to display the text back to the user you must decode it using the from_python method.
    This is because the package automatically encodes into base64 to protect against arbitrary SQL
    inject that may not otherwise be caught.

    the clean() function cleans out unwanted html tags and replaces newlines with <br> it also gets
        rid of any non-printable ascii characters
    hide_all_tags() completely removes anything that looks like html from the text
    '''
    __unpackargs__ = ('length','sql')

    htmlre = re.compile('''</?\w+((\s+\w+(\s*=\s*(?:".*?"|'.*?'|[^'">\s]+))?)+\s*|\s*)/?>''')
    all_chars = "".join([chr(i) for i in range(256)])
    non_printable = all_chars.translate(all_chars, string.printable)

    def getsql(self):
        if hasattr(self, 'sql'): return self.sql

    def allow_whitehtml(self, text):
        whitehtml = ['p', 'i', 'strong', 'b', 'u']
        lt = '&lt;'
        gt = '&gt;'
        for tag in whitehtml:
            while text.find(lt+tag+gt) != -1 and text.find(lt+'/'+tag+gt) != -1:
                text = text.replace(lt+tag+gt, '<'+tag+'>', 1)
                text = text.replace(lt+'/'+tag+gt, '</'+tag+'>', 1)
        return text

    def _to_python(self, value, state):
        msg = self.clean(value, True)
        msg = validators.MaxLength(self.length).to_python(msg)
        return base64.urlsafe_b64encode(msg)
    def _from_python(self, value, state):
        s = base64.urlsafe_b64decode(value)
        if self.getsql(): s = s.replace(';', '')
        return s

    def clean(self, text, whitehtml=False):
        import db
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        if whitehtml: text = self.allow_whitehtml(text)
        text = text.replace('\n', '<br>')
        text = text.replace('\r', '')
        text = text.translate(self.all_chars, self.non_printable)
        return text

    def hide_all_tags(self, text):
        g = self.htmlre.search(text)
        while g:
            text = text.replace(g.group(), '')
            g = self.htmlre.search(text)
        return text


#class SN_Exists(formencode.FancyValidator):
    #def _to_python(self, value, state):
        #import db
        #sn = validators.MaxLength(128).to_python(value)
        #sn = validators.PlainText(not_empty=True).to_python(sn)
        #con = db.connections.get_con()
        #cur = db.DictCursor(con)
        #cur.callproc('user_data_bysn', (sn,))
        #r = cur.fetchall()
        #cur.close()
        #db.connections.release_con(con)
        #if r: return sn
        #else:
            #raise formencode.Invalid('The screen_name supplied is not in the database.', sn, state)

def print_error(error):

    error = Text().clean(error)
    print_template("templates/error_template.html",  locals())

def print_template(template_path, namespace, ouf=sys.stdout):
    namespace = dict(namespace)
    f = open(template_path, 'r')
    s = f.readlines()
    f.close()

    if 'templater' not in namespace:
        import templater as __templater
        namespace.update({'templater':__templater})

    if '__ouf' not in namespace:
        namespace.update({'__ouf':ouf})
    ouf = namespace['__ouf']
    cop = yaptu.copier(__rex, namespace, __rbe, __ren, __rco, ouf=ouf)
    cop.copy(s)

def render(template_path, namespace):
    ouf = strio.StringIO()
    print_template(template_path, namespace, ouf)
    r = ouf.getvalue()
    ouf.close()
    return r

if __name__ == '__main__':
    print locals()
    print globals()
    print dir()
    print __templater_namespace

