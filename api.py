import os
import inspect
from parse import parse
from webob import Request, Response
from requests import Session as RequestSession
from wsgiadapter import WSGIAdapter as RequestWSGIAdapter
from jinja2 import Environment, FileSystemLoader

class API:
    def __init__(self, templates_dir="templates"):
        self._routes = {}
        self._templates_env = Environment(
            loader=FileSystemLoader(os.path.abspath(templates_dir))
        )

    def __call__(self, environ, start_response):
        request = Request(environ)

        response = self.handle_request(request)

        return response(environ, start_response)
    
    def test_session(self, base_url="http://testserver"):
        session = RequestSession()
        session.mount(prefix=base_url, adapter=RequestWSGIAdapter(self))
        return session
        
    def handle_request(self, request):
        response = Response()

        handler, kwargs = self._find_hadler(request_path=request.path)

        if handler is not None:
            if inspect.isclass(handler):
                handler = getattr(handler(), request.method.lower(), None)
                if handler is None:
                    raise AttributeError("Method not allowed", request.method)
            
            handler(request, response, **kwargs)  
        else:
            self.default_response(response)
        return response

    def _find_hadler(self, request_path):
        for path, handler in self._routes.items():
            parse_result = parse(path, request_path)
            if parse_result is not None:
                return handler, parse_result.named
        
        return None, None
    
    def add_route(self, path, handler):
        assert path not in self._routes, "Such route already exist"
        
        self._routes[path] = handler

    def route(self, path):
        def wrapper(handler):
            self.add_route(path, handler)
            return handler
        return wrapper

    def template(self, template_name, context=None):
        if context is None:
            context = {}
        return self._templates_env.get_template(template_name).render(**context)
    
    def default_response(self, response):
        response.status_code = 404
        response.text = "Not found"