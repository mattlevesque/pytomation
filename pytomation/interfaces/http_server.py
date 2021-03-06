import BaseHTTPServer
import base64
import threading
from SocketServer import ThreadingMixIn
from SimpleHTTPServer import SimpleHTTPRequestHandler
from pytomation.common import config
#import pytomation.common.config 
from pytomation.common.pyto_logging import PytoLogging
from pytomation.common.pytomation_api import PytomationAPI
from .ha_interface import HAInterface

file_path = "/tmp"

class PytoHandlerClass(SimpleHTTPRequestHandler):
    server = None

    def __init__(self,req, client_addr, server):
#        self._request = req
#        self._address = client_addr
        self._logger = PytoLogging(self.__class__.__name__)
        self._api = PytomationAPI()
        self._server = server

        SimpleHTTPRequestHandler.__init__(self, req, client_addr, server)

    def translate_path(self, path):
        global file_path
        path = file_path + path
        return path

    def do_HEAD(self):
        print "send header"
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_AUTHHEAD(self):
        print "send header"
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm=\"Test\"')
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        auth_credentials = base64.b64encode(config.admin_user + ":" + config.admin_password)
        
        if config.auth_enabled == 'Y' and self.headers.getheader('Authorization') == None:
            self.do_AUTHHEAD()
            self.wfile.write('no auth header received')
            return
        elif config.auth_enabled != 'Y' or self.headers.getheader('Authorization') == 'Basic ' + auth_credentials:
#            self.do_HEAD()
#            self.wfile.write(self.headers.getheader('Authorization'))
#            self.wfile.write('authenticated!')
            pass
        else:
            self.do_AUTHHEAD()
            self.wfile.write(self.headers.getheader('Authorization'))
            self.wfile.write('Not authenticated')
            self.wfile.write('<br />AuthConfig :' + config.auth_enabled)
            return
        self.route()

    def do_POST(self):
        self.route()

    def do_PUT(self):
        self.route()
        
    def do_DELETE(self):
        self.route()

    def do_ON(self):
        self.route()
        
    def do_OFF(self):
        self.route()

    def route(self):
        p = self.path.split('/')
        method = self.command
#        print "pd:" + self.path + ":" + str(p[1:])
        if p[1].lower() == "api":
            data = None
            if method.lower() == 'post':
                length = int(self.headers.getheader('content-length'))
                data = self.rfile.read(length)
#                print 'rrrrr' + str(length) + ":" + str(data) + 'fffff' + str(self._server)
                self.rfile.close()
            response = self._api.get_response(method=method, path="/".join(p[2:]), type=None, data=data, source=PytoHandlerClass.server)
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Content-length", len(response))
            self.end_headers()
            self.wfile.write(response)
            self.finish()
        else:
            getattr(SimpleHTTPRequestHandler, "do_" + self.command.upper())(self)

class ThreadedHTTPServer(ThreadingMixIn, BaseHTTPServer.HTTPServer):
    '''
    classdocs
    '''

class HTTPServer(HAInterface):
    def __init__(self, address=None, port=None, path=None, *args, **kwargs):
        super(HTTPServer, self).__init__(address, *args, **kwargs)
        self._handler_instances = []
        self.unrestricted = True # To override light object restrictions
    
    def _init(self, *args, **kwargs):
        super(HTTPServer, self)._init(*args, **kwargs)
        global file_path
        self._address = kwargs.get('address', config.http_address)
        self._port = kwargs.get('port', config.http_port)
        self._protocol = "HTTP/1.0"
        self._path = kwargs.get('path', config.http_path)
        file_path = self._path
        
    def run(self):
        server_address = (self._address, self._port)
        
        PytoHandlerClass.protocol_version = self._protocol
        PytoHandlerClass.server = self
        httpd = ThreadedHTTPServer(server_address, PytoHandlerClass)
        
        sa = httpd.socket.getsockname()
        print "Serving HTTP files at ", self._path, " on", sa[0], "port", sa[1], "..."
        httpd.serve_forever()
        #BaseHTTPServer.test(HandlerClass, ServerClass, protocol)

