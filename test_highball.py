import pytest

from api import API
from middleware import Middleware

FILE_DIR = "css"
FILE_NAME = "main.css"
FILE_CONTENTS = "body {background-color: red}"

# helpers

def _create_static(static_dir):
    asset = static_dir.mkdir(FILE_DIR).join(FILE_NAME)
    asset.write(FILE_CONTENTS)
    
    return asset

# tests

def test_basic_route_adding(api):
    @api.route("/home")
    def home(req,resp):
        resp.text = "YOLO"
        
def test_route_overlap_throws_exception(api):
    @api.route("/home")
    def home(req, resp):
        resp.text = "YOLO"
        
    with pytest.raises(AssertionError):
        @api.route("/home")
        def home2(req, resp):
            resp.text = "YOLO"

def test_highball_test_client_can_send_requests(api, client):
    RESPONSE_TEXT = "THIS IS COOL"
    
    @api.route("/hey/")
    def cool(req, resp):
        resp.text = RESPONSE_TEXT
        
    assert client.get("http://testserver/hey/").text == RESPONSE_TEXT
    
def test_parameterized_route(api, client):
    @api.route("/{name}")
    def hello(req, resp, name):
        resp.text = f'hey {name}'
        
    assert client.get("http://testserver/gyu").text == "hey gyu"
    assert client.get("http://testserver/123").text == "hey 123"

def test_default_404_response(client):
    resp = client.get("http://testserver/gyu")
    
    assert resp.status_code == 404
    assert resp.text == "Not found"
    
def test_class_based_handler_get(api, client):
    response_text = "this is a get request"
    
    @api.route("/book")
    class BookResource:
        def get(self, req, resp):
            resp.text = response_text
            
    assert client.get("http://testserver/book").text == response_text
    
def test_class_based_handler_post(api, client):
    response_text = "this is a post request"
    
    @api.route("/book")
    class BookResource:
        def post(self, req, resp):
            resp.text = response_text
        
    assert client.post("http://testserver/book").text == response_text

def test_class_based_handler_not_allowed_method(api, client):
    @api.route("/book")
    class BookResource:
        def post(self, req, resp):
            resp.text = "yolo"
    
    with pytest.raises(AttributeError):
        client.get("http://testserver/book")
        
def test_alternative_route(api, client):
    resp_text = "Alternative way to add a route"
    
    def home(req, resp):
        resp.text = resp_text
    
    api.add_route("/alternative", home)
    
    assert client.get("http://testserver/alternative").text == resp_text

def test_template(api, client):
    @api.route("/html")
    def html_handler(req, resp):
        resp.body = api.template("index.html", context={"title": "Some Title", "name": "Some Name"}).encode()
        
    resp = client.get("http://testserver/html")
    assert "text/html" in resp.headers["Content-Type"]
    assert "Some Title" in resp.text
    assert "Some Name" in resp.text
    
def test_custom_exception_handlr(api, client):
    def on_exception(req, resp, exc):
        resp.text = "AttributeErrorHappened"
    
    api.add_exception_handler(on_exception)
    
    @api.route("/")
    def index(req, resp):
        raise AttributeError()

    resp = client.get("http://testserver/")
    
    assert resp.text == "AttributeErrorHappened"
    
def test_404_is_returned_for_nonexistent_static_file(client):
    assert client.get(f"http://testserver/static/main.css)").status_code == 404
    
def test_assets_are_served(tmpdir_factory):
    static_dir = tmpdir_factory.mktemp("static")
    _create_static(static_dir=static_dir)
    api = API(static_dir=str(static_dir))
    client = api.test_session()
    
    response = client.get(f"http://testserver/static/{FILE_DIR}/{FILE_NAME}")
    
    assert response.status_code == 200
    assert response.text == FILE_CONTENTS
    
def test_middleware_methods_are_called(api, client):
    process_request_called = False
    process_response_called = False
    
    class CallMiddlewareMethods(Middleware):
        def __init__(self, app):
            super().__init__(app)
        
        def process_request(self, req):
            nonlocal process_request_called
            process_request_called = True
            
        def process_response(self, req, resp):
            nonlocal process_response_called
            process_response_called = True
            
    api.add_middleware(CallMiddlewareMethods)
    
    @api.route("/")
    def index(req, res):
        res.text = "YOLO"
    
    client.get("http://testserver/")
    
    assert process_request_called is True
    assert process_response_called is True
    

def test_allowed_methods_for_function_based_handlers(api, client):
    @api.route("/home", allowed_methods=["post"])
    def home(req, resp):
        resp.text = "Hello"
        
    with pytest.raises(AttributeError):
        client.get("http://testserver/home")
        
    assert client.post("http://testserver/home").text == "Hello"