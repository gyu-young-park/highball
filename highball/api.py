import os
import inspect
from parse import parse
from webob import Request
from requests import Session as RequestSession
from wsgiadapter import WSGIAdapter as RequestWSGIAdapter
from jinja2 import Environment, FileSystemLoader
from whitenoise import WhiteNoise
from .middleware import Middleware
from .response import Response

class API:
    def __init__(self, templates_dir="templates", static_dir="static"):
        self._routes = {}
        self._templates_env = Environment(
            loader=FileSystemLoader(os.path.abspath(templates_dir))
        )
        
        self.exception_handler = None
        
        self.whitenoise = WhiteNoise(self.wsgi_app, root=static_dir)
        
        self.middleware = Middleware(self)

    def __call__(self, environ, start_response):
        path_info = environ["PATH_INFO"]
        
        if path_info.startswith("/static"):
            environ["PATH_INFO"] = path_info[len("/static"):]
            return self.whitenoise(environ=environ, start_response=start_response)
        
        return self.middleware(environ=environ, start_response=start_response)
    
    def wsgi_app(self, environ, start_response):
        request = Request(environ)

        response = self.handle_request(request)

        return response(environ, start_response)
    
    def test_session(self, base_url="http://testserver"):
        session = RequestSession()
        session.mount(prefix=base_url, adapter=RequestWSGIAdapter(self))
        return session
        
    def handle_request(self, request):
        response = Response()

        handler_data, kwargs = self._find_hadler(request_path=request.path)
        try:
            if handler_data is not None:
                handler = handler_data["handler"]
                allowed_methods = handler_data["allowed_methods"]
                if inspect.isclass(handler):
                    handler = getattr(handler(), request.method.lower(), None)
                    if handler is None:
                        raise AttributeError("Method not allowed", request.method)
                else:
                    if request.method.lower() not in allowed_methods:
                        raise AttributeError("Method not allowed", request.method)
                
                handler(request, response, **kwargs)
            else:
                self.default_response(response)
        except Exception as e:
            if self.exception_handler is None:
                raise e
            else:
                self.exception_handler(request, response, e)
            
        return response

    def _find_hadler(self, request_path):
        for path, handler_date in self._routes.items():
            parse_result = parse(path, request_path)
            if parse_result is not None:
                return handler_date, parse_result.named
        
        return None, None
    
    def add_route(self, path, handler, allowed_methods=None):
        assert path not in self._routes, "Such route already exist"
        
        if allowed_methods is None:
            allowed_methods = ['get', 'post', 'put', 'delete', 'options']
            
        self._routes[path] = {"handler": handler, "allowed_methods": allowed_methods}

    def route(self, path, allowed_methods=None):
        def wrapper(handler):
            self.add_route(path, handler, allowed_methods)
            return handler
        return wrapper

    def template(self, template_name, context=None):
        if context is None:
            context = {}
        return self._templates_env.get_template(template_name).render(**context)
    
    def default_response(self, response):
        response.status_code = 404
        response.text = "Not found"
        
    def add_exception_handler(self, exception_handler):
        self.exception_handler = exception_handler
        
    def add_middleware(self, middleware_cls):
        self.middleware.add(middleware_cls)