from webob import Request

class Middleware:
    def __init__(self, app):
        self.app = app
    
    def __call__(self, environ, start_response):
        request = Request(environ=environ)
        response = self.app.handle_request(request)
        return response(environ, start_response)
    
    def add(self, middleware_cls):
        self.app = middleware_cls(self.app)
        
    def handle_request(self, request):
        self.process_request(req=request)
        response = self.app.handle_request(request)
        self.process_response(req=request, resp=response)
        
        return response
        
    def process_request(self, req):
        pass
    
    def process_response(self, req, resp):
        pass